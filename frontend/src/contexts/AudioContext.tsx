import React, { createContext, useContext, useState, useRef, useCallback, ReactNode, useEffect } from 'react';
import { io, Socket } from 'socket.io-client';
import { CarnaticAudioEngine, DetectionResult, AudioEngineConfig } from '../lib/analysis/engine';

// Use a more specific type for Carnatic pitch info
export type CarnaticPitchInfo = DetectionResult;

export interface AudioState {
  isRecording: boolean;
  isAnalyzing: boolean;
  currentPitch: CarnaticPitchInfo | null;
  audioLevel: number;
  error: string | null;
  deviceId: string | null;
  devices: MediaDeviceInfo[];
  isConnected: boolean; // WebSocket connection status
}

export interface AudioContextType extends AudioState {
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  startPitchDetection: () => Promise<void>;
  stopPitchDetection: () => void;
  setDevice: (deviceId: string) => Promise<void>;
  refreshDevices: () => Promise<void>;
  setBaseFrequency: (freq: number) => void;
}

const AudioContext = createContext<AudioContextType | undefined>(undefined);

export const useAudio = () => {
  const context = useContext(AudioContext);
  if (context === undefined) {
    throw new Error('useAudio must be used within an AudioProvider');
  }
  return context;
};

interface AudioProviderProps {
  children: ReactNode;
}

export const AudioProvider: React.FC<AudioProviderProps> = ({ children }) => {
  const [state, setState] = useState<AudioState>({
    isRecording: false,
    isAnalyzing: false,
    currentPitch: null,
    audioLevel: 0,
    error: null,
    deviceId: null,
    devices: [],
    isConnected: false,
  });

  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const microphoneRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const carnaticEngineRef = useRef<CarnaticAudioEngine | null>(null);
  const socketRef = useRef<Socket | null>(null);

  // Fetch config and initialize engine on mount
  useEffect(() => {
    const initialize = async () => {
      try {
        const response = await fetch('/api/v1/audio/config');
        if (!response.ok) {
          throw new Error('Failed to fetch audio configuration');
        }
        const config: AudioEngineConfig = await response.json();
        carnaticEngineRef.current = new CarnaticAudioEngine(config);
        
        initializeAudioContext(config.sampleRate);
        await refreshDevices();
        connectWebSocket();
      } catch (error) {
        setState(prev => ({ ...prev, error: error instanceof Error ? error.message : 'Initialization failed' }));
      }
    };

    initialize();

    return () => {
      cleanup();
    };
  }, []);

  const initializeAudioContext = (sampleRate: number) => {
    try {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      audioContextRef.current = new AudioContextClass({ sampleRate });
    } catch (error) {
      setState(prev => ({ ...prev, error: 'Failed to initialize audio context' }));
    }
  };

  const connectWebSocket = () => {
    // Assuming the server is on the same host
    const socket = io('http://localhost:5001');
    socketRef.current = socket;

    socket.on('connect', () => {
      setState(prev => ({ ...prev, isConnected: true }));
    });

    socket.on('disconnect', () => {
      setState(prev => ({ ...prev, isConnected: false }));
    });

    socket.on('error', (error) => {
      setState(prev => ({ ...prev, error: `WebSocket error: ${error.message}` }));
    });
  };

  const cleanup = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
    }
    if (socketRef.current) {
      socketRef.current.disconnect();
    }
  };

  const refreshDevices = async () => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const audioInputs = devices.filter(device => device.kind === 'audioinput');
      setState(prev => ({
        ...prev,
        devices: audioInputs,
        deviceId: audioInputs.length > 0 ? audioInputs[0].deviceId : null,
      }));
    } catch (error) {
      setState(prev => ({ ...prev, error: 'Failed to enumerate audio devices' }));
    }
  };

  const setDevice = async (deviceId: string) => {
    if (state.isRecording) {
      await stopRecording();
      setState(prev => ({ ...prev, deviceId }));
      await startRecording();
    } else {
      setState(prev => ({ ...prev, deviceId }));
    }
  };
  
  const setBaseFrequency = (freq: number) => {
    if (carnaticEngineRef.current) {
      carnaticEngineRef.current.setBaseSaFrequency(freq);
      // Optionally, notify the server
      if (socketRef.current?.connected) {
        socketRef.current.emit('set_base_frequency', { frequency: freq });
      }
    }
  };

  const startRecording = async () => {
    if (!audioContextRef.current || !carnaticEngineRef.current) {
      setState(prev => ({ ...prev, error: 'Audio engine not initialized' }));
      return;
    }
    if (audioContextRef.current.state === 'suspended') {
      await audioContextRef.current.resume();
    }

    try {
      const constraints = { audio: { deviceId: state.deviceId ? { exact: state.deviceId } : undefined, echoCancellation: false, noiseSuppression: false, autoGainControl: false } };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      mediaStreamRef.current = stream;

      const audioContext = audioContextRef.current;
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = carnaticEngineRef.current.getConfig().fftSize;
      
      const microphone = audioContext.createMediaStreamSource(stream);
      microphone.connect(analyser);

      analyserRef.current = analyser;
      microphoneRef.current = microphone;

      setState(prev => ({ ...prev, isRecording: true, error: null }));
    } catch (error) {
      setState(prev => ({ ...prev, error: error instanceof Error ? error.message : 'Failed to start recording' }));
      throw error;
    }
  };

  const stopRecording = () => {
    if (state.isAnalyzing) {
      stopPitchDetection();
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }
    if (microphoneRef.current) {
      microphoneRef.current.disconnect();
      microphoneRef.current = null;
    }
    setState(prev => ({ ...prev, isRecording: false, audioLevel: 0 }));
  };

  const analyzePitch = useCallback(() => {
    if (!analyserRef.current || !carnaticEngineRef.current) return;

    const analyser = analyserRef.current;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Float32Array(bufferLength);
    analyser.getFloatTimeDomainData(dataArray);

    const result = carnaticEngineRef.current.detectShruti(dataArray);

    let rms = 0;
    for (let i = 0; i < bufferLength; i++) {
      rms += dataArray[i] * dataArray[i];
    }
    const audioLevel = Math.sqrt(rms / bufferLength) * 100;

    setState(prev => ({ ...prev, currentPitch: result, audioLevel }));

    if (result && socketRef.current?.connected) {
      socketRef.current.emit('detection_result', result);
    }

    animationFrameRef.current = requestAnimationFrame(analyzePitch);
  }, []);

  const startPitchDetection = async () => {
    if (!state.isRecording) {
      await startRecording();
    }
    setState(prev => ({ ...prev, isAnalyzing: true }));
    animationFrameRef.current = requestAnimationFrame(analyzePitch);
  };

  const stopPitchDetection = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    setState(prev => ({ ...prev, isAnalyzing: false, currentPitch: null }));
  };

  const value: AudioContextType = {
    ...state,
    startRecording,
    stopRecording,
    startPitchDetection,
    stopPitchDetection,
    setDevice,
    refreshDevices,
    setBaseFrequency,
  };

  return (
    <AudioContext.Provider value={value}>
      {children}
    </AudioContext.Provider>
  );
};
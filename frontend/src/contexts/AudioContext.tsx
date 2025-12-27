import React, { createContext, useContext, useState, useRef, useCallback, ReactNode, useEffect } from 'react';
import { io, Socket } from 'socket.io-client';
import { CarnaticAudioEngine, DetectionResult, AudioEngineConfig } from '../lib/analysis/engine';

// Use a more specific type for Carnatic pitch info
export type CarnaticPitchInfo = DetectionResult;

// Practice feedback from server (when validating against exercise sequence)
export interface PracticeFeedback {
  shruti_name: string;
  frequency: number;
  cent_deviation: number;
  confidence: number;
  timestamp: number;
  expected_note?: string;
  next_note?: string;
  feedback_type?: 'correct' | 'incorrect';
  validation?: {
    expected_note: string;
    detected_note: string;
    position: number;
    total_notes: number;
    is_correct: boolean;
    accuracy_score: number;
    message: string;
    next_note?: string;  // Next expected note after correct answer
    completed?: boolean;
    final_score?: {
      total_notes: number;
      correct: number;
      incorrect: number;
      accuracy_percentage: number;
      grade: string;
    };
    progress: {
      current: number;
      total: number;
      percentage: number;
      correct: number;
      incorrect: number;
    };
  };
  progress?: {
    current: number;
    total: number;
    percentage: number;
    correct: number;
    incorrect: number;
  };
}

export interface AudioState {
  isRecording: boolean;
  isAnalyzing: boolean;
  currentPitch: CarnaticPitchInfo | null;
  audioLevel: number;
  error: string | null;
  deviceId: string | null;
  devices: MediaDeviceInfo[];
  isConnected: boolean; // WebSocket connection status
  practiceFeedback: PracticeFeedback | null; // Real-time feedback from server
  isPracticing: boolean; // Whether an exercise practice session is active
  practiceProgress: { current: number; total: number; percentage: number } | null;
}

export interface AudioContextType extends AudioState {
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  startPitchDetection: () => Promise<void>;
  stopPitchDetection: () => void;
  setDevice: (deviceId: string) => Promise<void>;
  refreshDevices: () => Promise<void>;
  setBaseFrequency: (freq: number) => void;
  // New methods for practice mode
  startPracticeSession: (pattern: {
    pattern_name: string;
    arohanam: string[];
    avarohanam: string[];
    include_avarohanam?: boolean;
  }) => void;
  stopPracticeSession: () => void;
  onPracticeFeedback: (callback: (feedback: PracticeFeedback) => void) => () => void;
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
    practiceFeedback: null,
    isPracticing: false,
    practiceProgress: null,
  });

  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const microphoneRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const carnaticEngineRef = useRef<CarnaticAudioEngine | null>(null);
  const socketRef = useRef<Socket | null>(null);
  const practiceFeedbackCallbacksRef = useRef<Set<(feedback: PracticeFeedback) => void>>(new Set());
  const scriptProcessorRef = useRef<ScriptProcessorNode | null>(null);

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
    // In development, connect directly to backend to avoid Vite proxy WebSocket issues
    // In production, use the same origin or configure via environment variable
    const isDev = import.meta.env.DEV;
    const wsUrl = import.meta.env.VITE_WS_URL || (isDev ? 'http://localhost:5002' : window.location.origin);
    console.log('Connecting to WebSocket at:', wsUrl);
    const socket = io(wsUrl, {
      path: '/socket.io',
      transports: ['polling', 'websocket'], // Start with polling, upgrade to websocket
    });
    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('WebSocket connected');
      setState(prev => ({ ...prev, isConnected: true, error: null }));
    });

    socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setState(prev => ({ ...prev, isConnected: false }));
    });

    socket.on('error', (error: any) => {
      console.error('WebSocket error:', error);
      setState(prev => ({ ...prev, error: `WebSocket error: ${error?.message || 'Unknown error'}` }));
    });

    // Listen for practice session started confirmation
    socket.on('practice_session_started', (data: any) => {
      console.log('Practice session started:', data);
      setState(prev => ({
        ...prev,
        isPracticing: true,
        practiceProgress: {
          current: 0,
          total: data.total_notes,
          percentage: 0
        }
      }));
    });

    // Listen for real-time practice feedback from server
    socket.on('practice_feedback', (feedback: PracticeFeedback) => {
      console.log('Practice feedback received:', feedback);
      setState(prev => ({
        ...prev,
        practiceFeedback: feedback,
        practiceProgress: feedback.progress || prev.practiceProgress
      }));

      // Notify all registered callbacks
      practiceFeedbackCallbacksRef.current.forEach(callback => {
        try {
          callback(feedback);
        } catch (e) {
          console.error('Error in practice feedback callback:', e);
        }
      });

      // Check if exercise completed
      if (feedback.validation?.completed) {
        setState(prev => ({ ...prev, isPracticing: false }));
      }
    });

    // Listen for shruti detection in free practice mode
    socket.on('shruti_detected', (data: any) => {
      // Update current pitch with server detection result
      // Map server snake_case to frontend camelCase for DetectionResult compatibility
      if (data.shruti_name) {
        setState(prev => ({
          ...prev,
          currentPitch: {
            shruti: { name: data.shruti_name, ratio: 1, westernEquiv: '', frequency: data.frequency },
            shrutiName: data.shruti_name, // Convenience property for direct access
            detectedFrequency: data.frequency,
            centDeviation: data.cent_deviation,
            confidence: data.confidence,
            timestamp: Date.now(),
          } as CarnaticPitchInfo
        }));
      }
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
    // Also stop script processor for audio streaming
    if (scriptProcessorRef.current) {
      scriptProcessorRef.current.disconnect();
      scriptProcessorRef.current = null;
    }
    setState(prev => ({ ...prev, isAnalyzing: false, currentPitch: null }));
  };

  // Start a practice session with a specific exercise pattern
  const startPracticeSession = (pattern: {
    pattern_name: string;
    arohanam: string[];
    avarohanam: string[];
    include_avarohanam?: boolean;
  }) => {
    if (!socketRef.current?.connected) {
      setState(prev => ({ ...prev, error: 'WebSocket not connected' }));
      return;
    }

    console.log('Starting practice session:', pattern);
    socketRef.current.emit('start_practice_session', {
      pattern_name: pattern.pattern_name,
      arohanam: pattern.arohanam,
      avarohanam: pattern.avarohanam,
      include_avarohanam: pattern.include_avarohanam ?? true,
    });

    setState(prev => ({
      ...prev,
      isPracticing: true,
      practiceFeedback: null,
      practiceProgress: null,
    }));
  };

  // Stop the current practice session
  const stopPracticeSession = () => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('end_exercise');
    }
    setState(prev => ({
      ...prev,
      isPracticing: false,
      practiceFeedback: null,
      practiceProgress: null,
    }));
  };

  // Subscribe to practice feedback events
  const onPracticeFeedback = (callback: (feedback: PracticeFeedback) => void) => {
    practiceFeedbackCallbacksRef.current.add(callback);
    // Return unsubscribe function
    return () => {
      practiceFeedbackCallbacksRef.current.delete(callback);
    };
  };

  // Stream audio to server for server-side pitch detection
  const startAudioStreaming = useCallback(() => {
    if (!audioContextRef.current || !microphoneRef.current || !socketRef.current?.connected) {
      console.log('Cannot start audio streaming - missing requirements');
      return;
    }

    const audioContext = audioContextRef.current;
    const bufferSize = 4096; // Approximately 85ms at 48kHz

    // Create script processor for audio streaming
    // Note: ScriptProcessorNode is deprecated but AudioWorklet requires more setup
    const scriptProcessor = audioContext.createScriptProcessor(bufferSize, 1, 1);
    scriptProcessorRef.current = scriptProcessor;

    scriptProcessor.onaudioprocess = (event) => {
      if (!socketRef.current?.connected || !state.isPracticing) return;

      const inputData = event.inputBuffer.getChannelData(0);

      // Convert to regular array for transmission
      // Downsample if needed to reduce bandwidth
      const audioArray = Array.from(inputData);

      // Send audio chunk to server for pitch detection
      socketRef.current.emit('audio_chunk', {
        audio_data: audioArray,
        sample_rate: audioContext.sampleRate,
        timestamp: Date.now(),
      });
    };

    // Connect microphone -> script processor -> destination (for monitoring)
    microphoneRef.current.connect(scriptProcessor);
    scriptProcessor.connect(audioContext.destination);

    console.log('Audio streaming started');
  }, [state.isPracticing]);

  // Effect to start/stop audio streaming when practice mode changes
  useEffect(() => {
    if (state.isPracticing && state.isRecording && microphoneRef.current) {
      startAudioStreaming();
    } else if (scriptProcessorRef.current) {
      scriptProcessorRef.current.disconnect();
      scriptProcessorRef.current = null;
    }
  }, [state.isPracticing, state.isRecording, startAudioStreaming]);

  const value: AudioContextType = {
    ...state,
    startRecording,
    stopRecording,
    startPitchDetection,
    stopPitchDetection,
    setDevice,
    refreshDevices,
    setBaseFrequency,
    startPracticeSession,
    stopPracticeSession,
    onPracticeFeedback,
  };

  return (
    <AudioContext.Provider value={value}>
      {children}
    </AudioContext.Provider>
  );
};
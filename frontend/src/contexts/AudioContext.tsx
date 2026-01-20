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

// Session Mode Types
export interface SessionExercise {
  name: string;
  arohanam: string[];
  avarohanam: string[];
}

export interface SessionProgress {
  current_exercise_index: number;
  total_exercises: number;
  exercises_completed: number;
  current_exercise_name: string;
  is_current_completed: boolean;
  session_active: boolean;
}

export interface ExerciseResult {
  index: number;
  name: string;
  total_notes: number;
  correct: number;
  incorrect: number;
  accuracy: number;
  grade: string;
}

export interface SessionSummary {
  total_exercises: number;
  exercises_completed: number;
  total_notes_played: number;
  total_correct_notes: number;
  total_incorrect_notes: number;
  session_accuracy: number;
  session_grade: string;
  session_duration_seconds: number;
  exercise_results: ExerciseResult[];
}

export type SessionEventType =
  | { type: 'session_mode_started'; data: { total_exercises: number; current_exercise_name: string; first_note: string } }
  | { type: 'session_exercise_advanced'; data: { current_exercise_index: number; current_exercise_name: string; first_note: string; previous_result?: ExerciseResult } }
  | { type: 'session_exercise_retried'; data: { current_exercise_name: string; first_note: string } }
  | { type: 'session_completed'; data: { summary: SessionSummary } }
  | { type: 'session_ended'; data: { summary: SessionSummary } }
  | { type: 'exercise_completed'; data: { exercise_name: string } };

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
  // Session Mode methods
  startSessionMode: (exercises: SessionExercise[]) => void;
  sessionRetryExercise: () => void;
  sessionNextExercise: () => void;
  sessionEnd: () => void;
  onSessionEvent: (callback: (event: SessionEventType) => void) => () => void;
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
  const sessionEventCallbacksRef = useRef<Set<(event: SessionEventType) => void>>(new Set());
  const scriptProcessorRef = useRef<ScriptProcessorNode | null>(null);
  const isPracticingRef = useRef<boolean>(false);  // Ref to avoid stale closure in audio callback
  const currentExercisePatternRef = useRef<{
    pattern_name: string;
    arohanam: string[];
    avarohanam: string[];
    include_avarohanam?: boolean;
  } | null>(null);  // Store current exercise for reconnection

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

      // Restore exercise state if we were practicing before reconnection
      if (isPracticingRef.current && currentExercisePatternRef.current) {
        console.log('Restoring exercise state after reconnection:', currentExercisePatternRef.current);
        socket.emit('start_practice_session', {
          pattern_name: currentExercisePatternRef.current.pattern_name,
          arohanam: currentExercisePatternRef.current.arohanam,
          avarohanam: currentExercisePatternRef.current.avarohanam,
          include_avarohanam: currentExercisePatternRef.current.include_avarohanam ?? true,
        });
      }
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

    // Session Mode Event Listeners
    socket.on('session_mode_started', (data: any) => {
      console.log('Session mode started:', data);

      // CRITICAL: Only start practicing AFTER server confirms session is ready
      // This ensures exercise_sequence is set before audio chunks are processed
      isPracticingRef.current = true;
      setState(prev => ({
        ...prev,
        isPracticing: true,
        practiceFeedback: null,
        practiceProgress: null,
      }));

      const event: SessionEventType = {
        type: 'session_mode_started',
        data: {
          total_exercises: data.total_exercises,
          current_exercise_name: data.current_exercise_name,
          first_note: data.first_note,
        }
      };
      sessionEventCallbacksRef.current.forEach(callback => {
        try { callback(event); } catch (e) { console.error('Error in session event callback:', e); }
      });
    });

    socket.on('session_exercise_advanced', (data: any) => {
      console.log('Session exercise advanced:', data);
      const event: SessionEventType = {
        type: 'session_exercise_advanced',
        data: {
          current_exercise_index: data.current_exercise_index,
          current_exercise_name: data.current_exercise_name,
          first_note: data.first_note,
          previous_result: data.previous_result ? {
            index: data.previous_result.exercise_index,
            name: data.previous_result.exercise_name,
            total_notes: data.previous_result.total_notes,
            correct: data.previous_result.correct_notes,
            incorrect: data.previous_result.incorrect_notes,
            accuracy: data.previous_result.accuracy_percentage,
            grade: data.previous_result.grade,
          } : undefined,
        }
      };
      sessionEventCallbacksRef.current.forEach(callback => {
        try { callback(event); } catch (e) { console.error('Error in session event callback:', e); }
      });
    });

    socket.on('session_exercise_retried', (data: any) => {
      console.log('Session exercise retried:', data);
      const event: SessionEventType = {
        type: 'session_exercise_retried',
        data: {
          current_exercise_name: data.current_exercise_name,
          first_note: data.first_note,
        }
      };
      sessionEventCallbacksRef.current.forEach(callback => {
        try { callback(event); } catch (e) { console.error('Error in session event callback:', e); }
      });
    });

    socket.on('session_completed', (data: any) => {
      console.log('Session completed:', data);
      const summary = data.summary;
      const event: SessionEventType = {
        type: 'session_completed',
        data: {
          summary: {
            total_exercises: summary.total_exercises,
            exercises_completed: summary.exercises_completed,
            total_notes_played: summary.total_notes_played,
            total_correct_notes: summary.total_correct_notes,
            total_incorrect_notes: summary.total_incorrect_notes,
            session_accuracy: summary.session_accuracy,
            session_grade: summary.session_grade,
            session_duration_seconds: summary.session_duration_seconds,
            exercise_results: summary.exercise_results.map((r: any) => ({
              index: r.exercise_index,
              name: r.exercise_name,
              total_notes: r.total_notes,
              correct: r.correct_notes,
              incorrect: r.incorrect_notes,
              accuracy: r.accuracy_percentage,
              grade: r.grade,
            })),
          }
        }
      };
      sessionEventCallbacksRef.current.forEach(callback => {
        try { callback(event); } catch (e) { console.error('Error in session event callback:', e); }
      });
    });

    socket.on('session_ended', (data: any) => {
      console.log('Session ended early:', data);
      const summary = data.summary;
      const event: SessionEventType = {
        type: 'session_ended',
        data: {
          summary: {
            total_exercises: summary.total_exercises,
            exercises_completed: summary.exercises_completed,
            total_notes_played: summary.total_notes_played,
            total_correct_notes: summary.total_correct_notes,
            total_incorrect_notes: summary.total_incorrect_notes,
            session_accuracy: summary.session_accuracy,
            session_grade: summary.session_grade,
            session_duration_seconds: summary.session_duration_seconds,
            exercise_results: summary.exercise_results.map((r: any) => ({
              index: r.exercise_index,
              name: r.exercise_name,
              total_notes: r.total_notes,
              correct: r.correct_notes,
              incorrect: r.incorrect_notes,
              accuracy: r.accuracy_percentage,
              grade: r.grade,
            })),
          }
        }
      };
      sessionEventCallbacksRef.current.forEach(callback => {
        try { callback(event); } catch (e) { console.error('Error in session event callback:', e); }
      });
    });

    // Listen for individual exercise completion during session mode
    socket.on('exercise_completed_in_session', (data: any) => {
      console.log('Exercise completed in session:', data);
      const event: SessionEventType = {
        type: 'exercise_completed',
        data: {
          exercise_name: data.exercise_name,
        }
      };
      sessionEventCallbacksRef.current.forEach(callback => {
        try { callback(event); } catch (e) { console.error('Error in session event callback:', e); }
      });
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

    // Store the pattern for reconnection recovery
    currentExercisePatternRef.current = pattern;

    socketRef.current.emit('start_practice_session', {
      pattern_name: pattern.pattern_name,
      arohanam: pattern.arohanam,
      avarohanam: pattern.avarohanam,
      include_avarohanam: pattern.include_avarohanam ?? true,
    });

    isPracticingRef.current = true;  // Update ref immediately for audio callback
    setState(prev => ({
      ...prev,
      isPracticing: true,
      practiceFeedback: null,
      practiceProgress: null,
    }));
  };

  // Stop the current practice session
  const stopPracticeSession = () => {
    isPracticingRef.current = false;  // Update ref immediately
    currentExercisePatternRef.current = null;  // Clear stored pattern
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

  // Session Mode Functions
  const startSessionMode = (exercises: SessionExercise[]) => {
    if (!socketRef.current?.connected) {
      setState(prev => ({ ...prev, error: 'WebSocket not connected' }));
      return;
    }

    console.log('Starting session mode with exercises:', exercises.map(e => e.name));
    socketRef.current.emit('start_session_mode', {
      exercises: exercises.map(ex => ({
        name: ex.name,
        arohanam: ex.arohanam,
        avarohanam: ex.avarohanam,
      })),
    });

    // NOTE: We DON'T set isPracticing = true here!
    // Audio streaming will start when 'session_mode_started' event is received from server.
    // This ensures the backend has the exercise_sequence context ready before
    // we start sending audio chunks for validation.
  };

  const sessionRetryExercise = () => {
    if (!socketRef.current?.connected) {
      setState(prev => ({ ...prev, error: 'WebSocket not connected' }));
      return;
    }

    console.log('Retrying current exercise');
    socketRef.current.emit('session_retry_exercise');

    setState(prev => ({
      ...prev,
      practiceFeedback: null,
      practiceProgress: null,
    }));
  };

  const sessionNextExercise = () => {
    if (!socketRef.current?.connected) {
      setState(prev => ({ ...prev, error: 'WebSocket not connected' }));
      return;
    }

    console.log('Advancing to next exercise');
    socketRef.current.emit('session_next_exercise');

    setState(prev => ({
      ...prev,
      practiceFeedback: null,
      practiceProgress: null,
    }));
  };

  const sessionEnd = () => {
    if (!socketRef.current?.connected) {
      setState(prev => ({ ...prev, error: 'WebSocket not connected' }));
      return;
    }

    console.log('Ending session');
    socketRef.current.emit('session_end');

    isPracticingRef.current = false;
    setState(prev => ({
      ...prev,
      isPracticing: false,
      practiceFeedback: null,
      practiceProgress: null,
    }));
  };

  const onSessionEvent = (callback: (event: SessionEventType) => void) => {
    sessionEventCallbacksRef.current.add(callback);
    // Return unsubscribe function
    return () => {
      sessionEventCallbacksRef.current.delete(callback);
    };
  };

  // Stream audio to server for server-side pitch detection
  const startAudioStreaming = useCallback(() => {
    if (!audioContextRef.current || !microphoneRef.current || !socketRef.current?.connected) {
      console.log('Cannot start audio streaming - missing requirements:', {
        hasAudioContext: !!audioContextRef.current,
        hasMicrophone: !!microphoneRef.current,
        socketConnected: socketRef.current?.connected
      });
      return;
    }

    const audioContext = audioContextRef.current;
    const bufferSize = 4096; // Approximately 85ms at 48kHz

    // Create script processor for audio streaming
    // Note: ScriptProcessorNode is deprecated but AudioWorklet requires more setup
    const scriptProcessor = audioContext.createScriptProcessor(bufferSize, 1, 1);
    scriptProcessorRef.current = scriptProcessor;

    scriptProcessor.onaudioprocess = (event) => {
      // Use ref instead of state to avoid stale closure
      if (!socketRef.current?.connected || !isPracticingRef.current) return;

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

    console.log('Audio streaming started - sending chunks to server');
  }, []); // No dependencies needed since we use refs

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
    // Session Mode
    startSessionMode,
    sessionRetryExercise,
    sessionNextExercise,
    sessionEnd,
    onSessionEvent,
  };

  return (
    <AudioContext.Provider value={value}>
      {children}
    </AudioContext.Provider>
  );
};
import { useState, useRef, useCallback, useEffect } from 'react';
import { Track, MusicPlayerState } from '@/types';

export function useMusicPlayer() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  
  const [state, setState] = useState<MusicPlayerState>({
    currentTrack: null,
    isPlaying: false,
    volume: 1,
    currentTime: 0,
    duration: 0,
    playlist: [],
    repeat: 'off',
    shuffle: false,
  });

  useEffect(() => {
    if (typeof window !== 'undefined') {
      audioRef.current = new Audio();
      
      const audio = audioRef.current;

      audio.addEventListener('loadedmetadata', () => {
        setState((prev) => ({ ...prev, duration: audio.duration }));
      });

      audio.addEventListener('timeupdate', () => {
        setState((prev) => ({ ...prev, currentTime: audio.currentTime }));
      });

      audio.addEventListener('ended', () => {
        handleTrackEnd();
      });

      audio.addEventListener('error', (e) => {
        console.error('Audio error:', e);
        setState((prev) => ({ ...prev, isPlaying: false }));
      });

      return () => {
        audio.pause();
        audio.src = '';
      };
    }
  }, []);

  const play = useCallback((track?: Track) => {
    if (!audioRef.current) return;

    if (track) {
      audioRef.current.src = track.audioUrl;
      setState((prev) => ({ ...prev, currentTrack: track, isPlaying: true }));
    } else {
      setState((prev) => ({ ...prev, isPlaying: true }));
    }

    audioRef.current.play();
  }, []);

  const pause = useCallback(() => {
    if (!audioRef.current) return;
    audioRef.current.pause();
    setState((prev) => ({ ...prev, isPlaying: false }));
  }, []);

  const togglePlay = useCallback(() => {
    if (state.isPlaying) {
      pause();
    } else {
      play();
    }
  }, [state.isPlaying, play, pause]);

  const seek = useCallback((time: number) => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = time;
    setState((prev) => ({ ...prev, currentTime: time }));
  }, []);

  const setVolume = useCallback((volume: number) => {
    if (!audioRef.current) return;
    const clampedVolume = Math.max(0, Math.min(1, volume));
    audioRef.current.volume = clampedVolume;
    setState((prev) => ({ ...prev, volume: clampedVolume }));
  }, []);

  const next = useCallback(() => {
    if (state.playlist.length === 0 || !state.currentTrack) return;

    const currentIndex = state.playlist.findIndex(
      (t) => t.id === state.currentTrack?.id
    );

    let nextIndex: number;

    if (state.shuffle) {
      nextIndex = Math.floor(Math.random() * state.playlist.length);
    } else {
      nextIndex = (currentIndex + 1) % state.playlist.length;
    }

    const nextTrack = state.playlist[nextIndex];
    play(nextTrack);
  }, [state.playlist, state.currentTrack, state.shuffle, play]);

  const previous = useCallback(() => {
    if (state.playlist.length === 0 || !state.currentTrack) return;

    // If more than 3 seconds played, restart current track
    if (state.currentTime > 3) {
      seek(0);
      return;
    }

    const currentIndex = state.playlist.findIndex(
      (t) => t.id === state.currentTrack?.id
    );

    const previousIndex =
      currentIndex === 0 ? state.playlist.length - 1 : currentIndex - 1;

    const previousTrack = state.playlist[previousIndex];
    play(previousTrack);
  }, [state.playlist, state.currentTrack, state.currentTime, play, seek]);

  const handleTrackEnd = useCallback(() => {
    if (state.repeat === 'one') {
      seek(0);
      play();
    } else if (state.repeat === 'all' || state.playlist.length > 1) {
      next();
    } else {
      pause();
    }
  }, [state.repeat, state.playlist, seek, play, next, pause]);

  const setPlaylist = useCallback((tracks: Track[], startIndex = 0) => {
    setState((prev) => ({ ...prev, playlist: tracks }));
    if (tracks.length > 0 && startIndex < tracks.length) {
      play(tracks[startIndex]);
    }
  }, [play]);

  const addToPlaylist = useCallback((track: Track) => {
    setState((prev) => ({
      ...prev,
      playlist: [...prev.playlist, track],
    }));
  }, []);

  const removeFromPlaylist = useCallback((trackId: string) => {
    setState((prev) => ({
      ...prev,
      playlist: prev.playlist.filter((t) => t.id !== trackId),
    }));
  }, []);

  const toggleRepeat = useCallback(() => {
    setState((prev) => {
      const modes: Array<'off' | 'one' | 'all'> = ['off', 'one', 'all'];
      const currentIndex = modes.indexOf(prev.repeat);
      const nextIndex = (currentIndex + 1) % modes.length;
      return { ...prev, repeat: modes[nextIndex] };
    });
  }, []);

  const toggleShuffle = useCallback(() => {
    setState((prev) => ({ ...prev, shuffle: !prev.shuffle }));
  }, []);

  return {
    ...state,
    play,
    pause,
    togglePlay,
    seek,
    setVolume,
    next,
    previous,
    setPlaylist,
    addToPlaylist,
    removeFromPlaylist,
    toggleRepeat,
    toggleShuffle,
  };
}

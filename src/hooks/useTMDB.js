import { useState, useEffect, useCallback } from 'react';
import { API_BASE_URL } from '../config';

const API_KEY = '909fc389a150847bdd4ffcd92809cff7';
const BASE_URL = 'https://api.themoviedb.org/3';
const IMAGE_BASE_URL = 'https://image.tmdb.org/t/p';

export const useTMDB = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async (endpoint) => {
    setLoading(true);
    setError(null);
    try {
      const isLocal = endpoint.startsWith('/api');
      const baseUrl = API_BASE_URL;
      const separator = endpoint.includes('?') ? '&' : '?';
      const url = isLocal 
        ? `${baseUrl}${endpoint}`
        : `${baseUrl}${endpoint}${separator}api_key=${API_KEY}&language=pt-BR`;

      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch');
      const data = await response.json();
      setLoading(false);
      return data;
    } catch (err) {
      setError(err.message);
      setLoading(false);
      return null;
    }
  }, []);

  return { fetchData, loading, error };
};

export const getImageUrl = (path, size = 'w500') => {
  if (!path) return null;
  const cleanPath = path.startsWith('/') ? path.substring(1) : path;
  return `${IMAGE_BASE_URL}/${size}/${cleanPath}`;
};

export const getBackdropUrl = (path) => getImageUrl(path, 'original');
export const getPosterUrl = (path) => getImageUrl(path, 'w500');

export const fetchCategories = {
  trending: '/trending/all/week',
  popular: '/movie/popular',
  topRated: '/movie/top_rated',
  upcoming: '/movie/upcoming',
  nowPlaying: '/movie/now_playing',
  action: '/discover/movie?with_genres=28&sort_by=popularity.desc',
  adventure: '/discover/movie?with_genres=12&sort_by=popularity.desc',
  animation: '/discover/movie?with_genres=16&sort_by=popularity.desc',
  comedy: '/discover/movie?with_genres=35&sort_by=popularity.desc',
  crime: '/discover/movie?with_genres=80&sort_by=popularity.desc',
  documentary: '/discover/movie?with_genres=99&sort_by=popularity.desc',
  drama: '/discover/movie?with_genres=18&sort_by=popularity.desc',
  family: '/discover/movie?with_genres=10751&sort_by=popularity.desc',
  fantasy: '/discover/movie?with_genres=14&sort_by=popularity.desc',
  history: '/discover/movie?with_genres=36&sort_by=popularity.desc',
  horror: '/discover/movie?with_genres=27&sort_by=popularity.desc',
  music: '/discover/movie?with_genres=10402&sort_by=popularity.desc',
  mystery: '/discover/movie?with_genres=9648&sort_by=popularity.desc',
  romance: '/discover/movie?with_genres=10749&sort_by=popularity.desc',
  scifi: '/discover/movie?with_genres=878&sort_by=popularity.desc',
  thriller: '/discover/movie?with_genres=53&sort_by=popularity.desc',
  war: '/discover/movie?with_genres=10752&sort_by=popularity.desc',
  western: '/discover/movie?with_genres=37&sort_by=popularity.desc',
  netflix: '/discover/movie?with_watch_providers=8&watch_region=US&sort_by=popularity.desc',
  disney: '/discover/movie?with_watch_providers=337&watch_region=US&sort_by=popularity.desc',
  hbo: '/discover/movie?with_watch_providers=384&watch_region=US&sort_by=popularity.desc',
  prime: '/discover/movie?with_watch_providers=9&watch_region=US&sort_by=popularity.desc',
  apple: '/discover/movie?with_watch_providers=350&watch_region=US&sort_by=popularity.desc',
};

export const genreMap = {
  28: 'Action',
  12: 'Adventure',
  16: 'Animation',
  35: 'Comedy',
  80: 'Crime',
  99: 'Documentary',
  18: 'Drama',
  10751: 'Family',
  14: 'Fantasy',
  36: 'History',
  27: 'Horror',
  10402: 'Music',
  9648: 'Mystery',
  10749: 'Romance',
  878: 'Science Fiction',
  10770: 'TV Movie',
  53: 'Thriller',
  10752: 'War',
  37: 'Western',
};
import { useState, useEffect, useCallback } from 'react';
import { 
  addToMyList, 
  removeFromMyList, 
  getMyList, 
  isInMyList,
  getCachedData,
  setCachedData,
  getCachedMovieDetails,
  setCachedMovieDetails
} from '../db';

// Hook for My List
export const useMyList = () => {
  const [myList, setMyList] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMyList();
  }, []);

  const loadMyList = async () => {
    try {
      const items = await getMyList();
      setMyList(items);
    } catch (error) {
      console.error('Error loading my list:', error);
    } finally {
      setLoading(false);
    }
  };

  const addMovie = async (movie) => {
    try {
      await addToMyList(movie);
      await loadMyList();
      return true;
    } catch (error) {
      console.error('Error adding to my list:', error);
      return false;
    }
  };

  const removeMovie = async (movieId) => {
    try {
      await removeFromMyList(movieId);
      await loadMyList();
      return true;
    } catch (error) {
      console.error('Error removing from my list:', error);
      return false;
    }
  };

  const checkIsInList = async (movieId) => {
    try {
      return await isInMyList(movieId);
    } catch (error) {
      console.error('Error checking my list:', error);
      return false;
    }
  };

  return {
    myList,
    loading,
    addMovie,
    removeMovie,
    checkIsInList,
    refresh: loadMyList
  };
};

// Hook for cached API calls
export const useCachedAPI = (fetchData) => {
  const fetchWithCache = useCallback(async (endpoint) => {
    // Try to get from cache first
    const cached = await getCachedData(endpoint);
    if (cached) {
      console.log(`Cache hit for ${endpoint}`);
      return cached;
    }

    // If not in cache, fetch from API
    console.log(`Cache miss for ${endpoint}, fetching from API...`);
    const data = await fetchData(endpoint);
    
    if (data) {
      // Store in cache
      await setCachedData(endpoint, data);
    }
    
    return data;
  }, [fetchData]);

  const fetchMovieDetailsWithCache = useCallback(async (movieId, fetchFn) => {
    const cached = await getCachedMovieDetails(movieId);
    if (cached) {
      return cached;
    }

    const data = await fetchFn();
    if (data) {
      await setCachedMovieDetails(movieId, data);
    }
    
    return data;
  }, []);

  return {
    fetchWithCache,
    fetchMovieDetailsWithCache
  };
};
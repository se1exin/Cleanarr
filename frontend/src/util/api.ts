/**
 * API Handlers
 */

import axios from 'axios';

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:5000";

const DUPES_URL = `${BACKEND_URL}/movies/dupes`;
const SAMPLES_URL = `${BACKEND_URL}/movies/samples`;
const DELETE_MEDIA_URL = `${BACKEND_URL}/delete/media`;

export const getDupeMovies = (): Promise<any> => {
  return axios.get(DUPES_URL);
};

export const getSampleMovies = (): Promise<any> => {
  return axios.get(SAMPLES_URL);
};

export const deleteMedia = (movieKey: string, mediaId: number): Promise<any> => {
  return axios.post(DELETE_MEDIA_URL, {
    'movie_key': movieKey,
    'media_id': mediaId
  })
};

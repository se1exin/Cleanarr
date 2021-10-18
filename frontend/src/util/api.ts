/**
 * API Handlers
 */

import axios from 'axios';

export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:5000/";

const INFO_URL = `${BACKEND_URL}server/info`;
const DUPES_URL = `${BACKEND_URL}content/dupes`;
const SAMPLES_URL = `${BACKEND_URL}content/samples`;
const DELETE_MEDIA_URL = `${BACKEND_URL}delete/media`;

export const getServerInfo = (): Promise<any> => {
  return axios.get(INFO_URL);
};

export const getDupeContent = (): Promise<any> => {
  return axios.get(DUPES_URL);
};

export const getSampleContent = (): Promise<any> => {
  return axios.get(SAMPLES_URL);
};

export const deleteMedia = (contentKey: string, mediaId: number): Promise<any> => {
  return axios.post(DELETE_MEDIA_URL, {
    'content_key': contentKey,
    'media_id': mediaId
  })
};

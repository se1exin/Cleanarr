/**
 * API Handlers
 */

import axios from 'axios';

export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:5000/";

const INFO_URL = `${BACKEND_URL}server/info`;
const DELETED_SIZES = `${BACKEND_URL}server/deleted-sizes`;
const DUPES_URL = `${BACKEND_URL}content/dupes`;
const SAMPLES_URL = `${BACKEND_URL}content/samples`;
const DELETE_MEDIA_URL = `${BACKEND_URL}delete/media`;
const IGNORE_MEDIA_URL = `${BACKEND_URL}content/ignore`;

export const getServerInfo = (): Promise<any> => {
  return axios.get(INFO_URL);
};

export const getDeletedSizes = (): Promise<any> => {
  return axios.get(DELETED_SIZES);
};

export const getDupeContent = (): Promise<any> => {
  return axios.get(DUPES_URL);
};

export const getSampleContent = (): Promise<any> => {
  return axios.get(SAMPLES_URL);
};

export const deleteMedia = (library: string, contentKey: string, mediaId: number): Promise<any> => {
  return axios.post(DELETE_MEDIA_URL, {
    'library_name': library,
    'content_key': contentKey,
    'media_id': mediaId
  })
};

export const ignoreMedia = (contentKey: string): Promise<any> => {
  return axios.post(IGNORE_MEDIA_URL, {
    'content_key': contentKey
  })
};

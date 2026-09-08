import axios from 'axios';
const API_BASE = 'http://localhost:8000';
export const generatePaper = (data) => axios.post(`${API_BASE}/generate`, data);
export const getStatus = (jobId) => axios.get(`${API_BASE}/status/${jobId}`);
export const getDownloadUrl = (jobId) => `${API_BASE}/download/${jobId}`;
export const getPreviewUrl = (jobId) => `${API_BASE}/preview/${jobId}`;

import api from './client'

export const register = (email, nome, senha) =>
  api.post('/auth/register', { email, nome, senha })

export const login = (email, senha) =>
  api.post('/auth/login', { email, senha })

export const getMe = () =>
  api.get('/auth/me')

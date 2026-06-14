const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(error.detail || '请求失败')
  }

  return response.json()
}

export const api = {
  getCourts: () => request('/courts'),
  createCourt: (payload) =>
    request('/courts', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  getMembers: () => request('/members'),
  getTimeSlots: (date, courtId) =>
    request(`/time-slots${date || courtId ? '?' : ''}${date ? `date=${date}` : ''}${date && courtId ? '&' : ''}${courtId ? `court_id=${courtId}` : ''}`),
  createTimeSlot: (payload) =>
    request('/time-slots', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  generateTimeSlots: (payload) =>
    request('/time-slots/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  updateTimeSlot: (slotId, payload) =>
    request(`/time-slots/${slotId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),
  getBookings: () => request('/bookings'),
  createBooking: (payload) =>
    request('/bookings', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  settleBooking: (bookingId) =>
    request(`/bookings/${bookingId}/settle`, {
      method: 'POST',
    }),
  cancelBooking: (bookingId) =>
    request(`/bookings/${bookingId}/cancel`, {
      method: 'POST',
    }),
}

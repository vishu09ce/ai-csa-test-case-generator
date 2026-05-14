export function parseApiError(err) {
  if (err?.response?.data?.detail) {
    return err.response.data.detail
  }
  if (err?.message) {
    return err.message
  }
  return 'An unexpected error occurred. Please try again.'
}

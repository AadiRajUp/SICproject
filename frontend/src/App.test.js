import { render, screen } from '@testing-library/react';
import App from './App';

test('renders navbar brand', () => {
  render(<App />);
  expect(screen.getByText(/FDS Dashboard/i)).toBeInTheDocument();
});

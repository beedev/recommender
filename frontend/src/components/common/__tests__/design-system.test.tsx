/**
 * Basic test to verify our design system components can be imported and rendered
 */
import { render } from '@testing-library/react'
import '@testing-library/jest-dom'

// Import our design system components
import {
  Avatar,
  Badge,
  Button,
  Input,
  LoadingSpinner,
  Textarea,
} from '../index'

describe('Design System Components', () => {
  test('Avatar component renders', () => {
    const { container } = render(<Avatar fallback="Test User" />)
    expect(container.firstChild).toBeInTheDocument()
  })

  test('Badge component renders', () => {
    const { container } = render(<Badge>Test Badge</Badge>)
    expect(container.firstChild).toBeInTheDocument()
  })

  test('Button component renders', () => {
    const { container } = render(<Button>Test Button</Button>)
    expect(container.firstChild).toBeInTheDocument()
  })

  test('Input component renders', () => {
    const { container } = render(<Input placeholder="Test input" />)
    expect(container.firstChild).toBeInTheDocument()
  })

  test('LoadingSpinner component renders', () => {
    const { container } = render(<LoadingSpinner />)
    expect(container.firstChild).toBeInTheDocument()
  })

  test('Textarea component renders', () => {
    const { container } = render(<Textarea placeholder="Test textarea" />)
    expect(container.firstChild).toBeInTheDocument()
  })
})
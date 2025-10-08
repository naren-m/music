import clsx, { ClassValue } from 'clsx'

/**
 * Utility function for combining class names with support for conditional classes
 * Uses clsx for conditional class handling
 */
export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

export default cn
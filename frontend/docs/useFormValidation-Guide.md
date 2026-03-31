# useFormValidation Hook Guide

Complete guide for using the `useFormValidation` hook to simplify form validation in your components.

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Basic Usage](#basic-usage)
4. [Built-in Validators](#built-in-validators)
5. [Single Field Validation](#single-field-validation)
6. [Multi-Field Validation](#multi-field-validation)
7. [Migration Examples](#migration-examples)
8. [Best Practices](#best-practices)

---

## Overview

`useFormValidation` is a React hook that consolidates form validation logic into a reusable, type-safe interface. It eliminates repetitive validation code and provides a consistent pattern for all forms.

**Benefits:**
- ✅ Reduces boilerplate by 40-60%
- ✅ Automatic error clearing on input change
- ✅ Built-in sanitization support
- ✅ Composable validation rules
- ✅ Full TypeScript support
- ✅ Single & multi-field modes

---

## Installation

The hook is already available in your project:

```typescript
import { useFormValidation, validators } from '../hooks/useFormValidation'
```

---

## Basic Usage

### Single Field (Simple)

```typescript
const { error, validate, handleChange, handleBlur } = useFormValidation({
  value: productName,
  onChange: setProductName,
  validators: [
    validators.required('Product name is required'),
    validators.length(2, 100, 'Product name')
  ]
})

// In render:
<input
  value={productName}
  onChange={(e) => handleChange(e.target.value)}
  onBlur={handleBlur}
/>
{error && <span className="error">{error}</span>}

// On submit:
if (!validate()) return
```

### Multi-Field (Complex)

```typescript
const { errors, validateAll, getFieldProps } = useFormValidation({
  fields: {
    email: {
      value: email,
      onChange: setEmail,
      validators: [validators.required(), validators.pattern(/^\S+@\S+$/, 'Invalid email')]
    },
    password: {
      value: password,
      onChange: setPassword,
      validators: [validators.minLength(6, 'Password')]
    }
  }
})

// In render:
<input {...getFieldProps('email')} />
{errors.email && <span>{errors.email}</span>}

// On submit:
if (!validateAll()) return
```

---

## Built-in Validators

All validators return `true` on success or an error message string on failure.

### `validators.required(message?)`
Validates that field is not empty.

```typescript
validators.required('This field is required')
```

### `validators.length(min, max, fieldName?)`
Validates string length between min and max.

```typescript
validators.length(2, 100, 'Product name')
// Error: "Product name must be at least 2 characters"
```

### `validators.minLength(min, fieldName?)`
Validates minimum string length.

```typescript
validators.minLength(6, 'Password')
// Error: "Password must be at least 6 characters"
```

### `validators.alphanumeric(allowedChars?, fieldName?, allowUnicode?)`
Validates alphanumeric with optional special characters.

```typescript
validators.alphanumeric('- _&\'', 'Store name', true)
// Allows: letters, numbers, hyphens, underscores, ampersands, apostrophes
```

### `validators.decimal(min, max, decimals?, fieldName?)`
Validates decimal numbers.

```typescript
validators.decimal(0.01, 999999.99, 2, 'Price')
// Validates price between 0.01 and 999999.99 with max 2 decimal places
```

### `validators.pattern(regex, message)`
Custom regex validation.

```typescript
validators.pattern(/^[a-zA-Z0-9_-]+$/, 'Username can only contain letters, numbers, underscores and hyphens')
```

### `validators.match(otherValue, message)`
Validates that two fields match (for password confirmation).

```typescript
validators.match(password, 'Passwords do not match')
```

### `validators.custom(fn)`
Custom validation function.

```typescript
validators.custom((value) => {
  if (value === 'admin') return 'Username "admin" is reserved'
  return true
})
```

---

## Single Field Validation

Use single field mode for forms with one validated input or when you want independent field validation.

### Full API

```typescript
const {
  error,           // string: Current validation error
  validate,        // () => boolean: Run validation manually
  clearError,      // () => void: Clear error manually
  handleChange,    // (value: string) => void: Handle input change with auto-clear
  handleBlur       // () => void: Handle blur with optional validation
} = useFormValidation({
  value: string,              // Current field value
  onChange: (v: string) => void,  // Setter function
  validators?: Validator[],   // Array of validation functions
  sanitize?: (v: string) => string,  // Optional sanitization function
  validateOnBlur?: boolean    // Validate on blur (default: false)
})
```

### Example: NewGroupPopup

**Before (46 lines):**
```typescript
const [groupName, setGroupName] = useState('')
const [error, setError] = useState('')

const validateGroupName = (value: string): boolean => {
  setError('')
  const trimmed = value.trim()

  if (trimmed.length === 0) {
    setError(t('groups:validation.nameRequired'))
    return false
  }

  const lengthValidation = validateLength(trimmed, 2, 100, t('groups:fields.name'))
  if (!lengthValidation.isValid) {
    setError(lengthValidation.error || t('groups:validation.invalidName'))
    return false
  }

  const alphanumericValidation = validateAlphanumeric(trimmed, '- _&\'', t('groups:fields.name'))
  if (!alphanumericValidation.isValid) {
    setError(alphanumericValidation.error || t('groups:validation.invalidCharacters'))
    return false
  }

  return true
}

const handleNameChange = (value: string) => {
  const sanitized = sanitizeString(value, 100)
  setGroupName(sanitized)
  setError('')
}

const handleBlur = () => {
  if (groupName.trim()) {
    validateGroupName(groupName)
  }
}

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault()
  if (!validateGroupName(groupName)) return
  // ... submit logic
}

<input
  value={groupName}
  onChange={(e) => handleNameChange(e.target.value)}
  onBlur={handleBlur}
/>
```

**After (15 lines):**
```typescript
const [groupName, setGroupName] = useState('')

const { error, validate, handleChange, handleBlur } = useFormValidation({
  value: groupName,
  onChange: setGroupName,
  validators: [
    validators.required(t('groups:validation.nameRequired')),
    validators.length(2, 100, t('groups:fields.name')),
    validators.alphanumeric('- _&\'', t('groups:fields.name'))
  ],
  sanitize: (v) => sanitizeString(v, 100),
  validateOnBlur: true
})

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault()
  if (!validate()) return
  // ... submit logic
}

<input
  value={groupName}
  onChange={(e) => handleChange(e.target.value)}
  onBlur={handleBlur}
/>
```

**Savings: 31 lines (67% reduction)**

---

## Multi-Field Validation

Use multi-field mode for forms with multiple validated inputs.

### Full API

```typescript
const {
  errors,              // Record<string, string>: Errors by field name
  validateField,       // (fieldName: string) => boolean: Validate one field
  validateAll,         // () => boolean: Validate all fields
  clearFieldError,     // (fieldName: string) => void: Clear one field error
  clearAllErrors,      // () => void: Clear all errors
  getFieldProps        // (fieldName: string) => object: Get input props
} = useFormValidation({
  fields: {
    [fieldName]: {
      value: string,
      onChange: (v: string) => void,
      validators?: Validator[],
      sanitize?: (v: string) => string,
      validateOnBlur?: boolean
    }
  }
})
```

### Example: Password Change

```typescript
const [newPassword, setNewPassword] = useState('')
const [confirmPassword, setConfirmPassword] = useState('')

const { errors, validateAll } = useFormValidation({
  fields: {
    newPassword: {
      value: newPassword,
      onChange: setNewPassword,
      validators: [
        validators.minLength(6, 'Password')
      ]
    },
    confirmPassword: {
      value: confirmPassword,
      onChange: setConfirmPassword,
      validators: [
        validators.match(newPassword, 'Passwords do not match')
      ]
    }
  }
})

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault()
  if (!validateAll()) return
  // ... submit logic
}

// Display combined error
const displayError = errors.newPassword || errors.confirmPassword

<BaseModal error={displayError}>
  <input
    type="password"
    value={newPassword}
    onChange={(e) => setNewPassword(e.target.value)}
  />

  <input
    type="password"
    value={confirmPassword}
    onChange={(e) => setConfirmPassword(e.target.value)}
  />
</BaseModal>
```

### Using getFieldProps (Advanced)

```typescript
const { getFieldProps } = useFormValidation({
  fields: {
    email: {
      value: email,
      onChange: setEmail,
      validators: [validators.required()],
      validateOnBlur: true
    }
  }
})

// Automatically handles value, onChange, onBlur, error
<input {...getFieldProps('email')} type="email" />
```

---

## Migration Examples

### From: Manual Validation

**Before:**
```typescript
const [productName, setProductName] = useState('')
const [error, setError] = useState('')

const validateProductName = (value: string): boolean => {
  setError('')
  const trimmed = value.trim()

  if (trimmed.length === 0) {
    setError('Product name is required')
    return false
  }

  if (trimmed.length < 2 || trimmed.length > 100) {
    setError('Product name must be between 2 and 100 characters')
    return false
  }

  return true
}

const handleChange = (value: string) => {
  setProductName(value)
  setError('')
}
```

**After:**
```typescript
const [productName, setProductName] = useState('')

const { error, validate, handleChange } = useFormValidation({
  value: productName,
  onChange: setProductName,
  validators: [
    validators.required('Product name is required'),
    validators.length(2, 100, 'Product name')
  ]
})
```

### From: Inline Validation

**Before:**
```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault()
  setError('')

  if (username.length < 3) {
    setError('Username must be at least 3 characters')
    return
  }

  if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
    setError('Username can only contain letters, numbers, underscores and hyphens')
    return
  }

  // ... submit
}
```

**After:**
```typescript
const { error, validate } = useFormValidation({
  value: username,
  onChange: setUsername,
  validators: [
    validators.minLength(3, 'Username'),
    validators.pattern(/^[a-zA-Z0-9_-]+$/, 'Username can only contain letters, numbers, underscores and hyphens')
  ]
})

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault()
  if (!validate()) return
  // ... submit
}
```

---

## Best Practices

### 1. Separate Validation Errors from Server Errors

```typescript
const [serverError, setServerError] = useState('')
const { error, validate } = useFormValidation({ /* ... */ })

// In BaseModal
<BaseModal error={error || serverError}>
```

### 2. Use validateOnBlur for Better UX

```typescript
useFormValidation({
  value: storeName,
  onChange: setStoreName,
  validators: [/* ... */],
  validateOnBlur: true  // Validate when user leaves field
})
```

### 3. Sanitize Input for Length Limits

```typescript
useFormValidation({
  value: productName,
  onChange: setProductName,
  validators: [/* ... */],
  sanitize: (v) => sanitizeString(v, 100)  // Limit to 100 chars
})
```

### 4. Compose Validators

```typescript
const productNameValidators = [
  validators.required(t('product:validation.nameRequired')),
  validators.length(2, 100, t('product:fields.name')),
  validators.alphanumeric('- _&\'(),.', t('product:fields.name'), true)
]

useFormValidation({
  value: productName,
  onChange: setProductName,
  validators: productNameValidators
})
```

### 5. Custom Validators for Business Logic

```typescript
useFormValidation({
  value: storeName,
  onChange: setStoreName,
  validators: [
    validators.required(),
    validators.length(2, 100),
    validators.custom((value) => {
      // Check for duplicate store names
      const exists = stores.some(s => s.name.toLowerCase() === value.toLowerCase())
      return exists ? 'Store name already exists' : true
    })
  ]
})
```

### 6. Combine with Other Validation Logic

```typescript
const { error, validate } = useFormValidation({ /* ... */ })

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault()

  // Run hook validation first
  if (!validate()) return

  // Then run additional checks
  if (exactMatch) {
    setServerError('Exact match found')
    return
  }

  // Submit
}
```

---

## Common Patterns

### Optional Fields

```typescript
validators.decimal(0.01, 999999.99, 2, 'Price')  // Allows empty string
```

### Required Numeric Fields

```typescript
validators.custom((value) => {
  if (!value.trim()) return 'Quantity is required'
  const num = parseFloat(value)
  if (isNaN(num) || num <= 0) return 'Quantity must be greater than 0'
  return true
})
```

### Conditional Validation

```typescript
const validators = [
  validators.required(),
  ...(requiresEmail ? [validators.pattern(/^\S+@\S+$/, 'Invalid email')] : [])
]
```

### Dynamic Error Messages

```typescript
validators.length(
  MIN_LENGTH,
  MAX_LENGTH,
  t('fields.productName')  // Translatable field name
)
```

---

## TypeScript Tips

### Type-Safe Field Names

```typescript
type FormFields = 'email' | 'password' | 'confirmPassword'

const { getFieldProps } = useFormValidation<FormFields>({
  fields: {
    email: { /* ... */ },
    password: { /* ... */ },
    confirmPassword: { /* ... */ }
  }
})

// TypeScript ensures correct field names
getFieldProps('email')  // ✅
getFieldProps('invalid')  // ❌ Type error
```

### Custom Validator Types

```typescript
const myValidator: Validator = (value: string) => {
  // Your validation logic
  return true // or error string
}
```

---

## Troubleshooting

### Error Not Clearing on Change

**Problem:** Error persists after typing.

**Solution:** Use `handleChange` from hook instead of direct onChange:

```typescript
// ❌ Wrong
<input onChange={(e) => setField(e.target.value)} />

// ✅ Correct
<input onChange={(e) => handleChange(e.target.value)} />
```

### Validation Running Too Early

**Problem:** Validation triggers before user finishes typing.

**Solution:** Use `validateOnBlur` instead of inline validation:

```typescript
useFormValidation({
  /* ... */,
  validateOnBlur: true  // Only validate when field loses focus
})
```

### Multiple Error Messages

**Problem:** Want to show first error only.

**Solution:** Hook already returns first error. For multi-field:

```typescript
const displayError = errors.field1 || errors.field2 || errors.field3
```

---

## Performance Tips

1. **Memoize Validators:**
   ```typescript
   const validators = useMemo(() => [
     validators.required(),
     validators.length(2, 100)
   ], [])
   ```

2. **Debounce API Checks:**
   ```typescript
   useEffect(() => {
     const timer = setTimeout(() => {
       // Check for duplicates
     }, 300)
     return () => clearTimeout(timer)
   }, [fieldValue])
   ```

3. **Separate Validation from Rendering:**
   ```typescript
   // Validation hooks at top
   const { error, validate } = useFormValidation({ /* ... */ })

   // Expensive renders below
   ```

---

## Next Steps

- **Migrate remaining popups:** NewProductPopup, EditProductPopup, EditStorePopup, EditUserPopup, BidPopup
- **Add new validators:** Email, URL, phone number
- **Create form builder:** Wrapper component for common form patterns
- **Add unit tests:** Test individual validators independently

---

## Questions?

- Check migrated examples: NewGroupPopup, NewStorePopup, ChangeUsernamePopup, ChangePasswordPopup
- Read hook source: `frontend/src/hooks/useFormValidation.ts`
- Review validation utilities: `frontend/src/utils/validation.ts`

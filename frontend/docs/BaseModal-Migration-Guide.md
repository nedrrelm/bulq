# BaseModal Migration Guide

This guide helps you migrate existing popup components to use the new `BaseModal` component.

## Why Migrate?

**Benefits:**
- **Reduced boilerplate**: Each popup is ~20-30 lines shorter
- **Consistent behavior**: Modal overlay, focus trap, and error handling work the same everywhere
- **Type safety**: Full TypeScript support with comprehensive props
- **Easier maintenance**: Bug fixes and improvements in one place
- **Better accessibility**: Focus trap and keyboard handling built-in

**Proven Results:**
- ChangeNamePopup: 113 → 89 lines (21% reduction)
- NewGroupPopup: 137 → 113 lines (18% reduction)
- ForceConfirmPopup: 90 → 66 lines (27% reduction)

---

## Quick Migration Checklist

1. ✅ Import `BaseModal` instead of `useModalFocusTrap`
2. ✅ Remove `useRef` and `modalRef` (handled by BaseModal)
3. ✅ Remove `useModalFocusTrap` call
4. ✅ Replace modal overlay structure with `<BaseModal>` wrapper
5. ✅ Move title to `title` prop
6. ✅ Move error display to `error` prop
7. ✅ Move action buttons to `submitButton` and `cancelButton` props
8. ✅ Keep form content as children

---

## Migration Pattern

### Before (Old Pattern)

```tsx
import { useState, useRef } from 'react'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'

export default function MyPopup({ onClose, onSuccess }) {
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const modalRef = useRef<HTMLDivElement>(null)

  useModalFocusTrap(modalRef, true, onClose)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    // ... submit logic
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div ref={modalRef} className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Title</h2>
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          {/* Form fields here */}

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Submitting...' : 'Submit'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
```

### After (Using BaseModal)

```tsx
import { useState } from 'react'
import BaseModal from './BaseModal'

export default function MyPopup({ onClose, onSuccess }) {
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    // ... submit logic
  }

  return (
    <BaseModal
      isOpen={true}
      onClose={onClose}
      title="Title"
      error={error}
      submitButton={{
        text: submitting ? 'Submitting...' : 'Submit',
        onClick: handleSubmit,
        loading: submitting,
        disabled: submitting
      }}
    >
      {/* Form fields here - same as before */}
    </BaseModal>
  )
}
```

**Key Changes:**
- ❌ Remove: `useRef`, `modalRef`, `useModalFocusTrap`, modal overlay structure, error div, modal-actions div
- ✅ Add: `BaseModal` wrapper with props
- ✅ Keep: Form fields, validation logic, state management

---

## Common Scenarios

### 1. Simple Form (Example: ChangeNamePopup)

**Use Case:** Basic form with validation and submit button

```tsx
<BaseModal
  isOpen={true}
  onClose={onClose}
  title={t('profile:changeName.title')}
  error={error}
  submitButton={{
    text: submitting ? t('profile:changeName.changing') : t('common:buttons.save'),
    onClick: handleSubmit,
    loading: submitting,
    disabled: submitting
  }}
>
  <div className="form-group">
    <label htmlFor="new-name">{t('profile:fields.name')} *</label>
    <input
      id="new-name"
      type="text"
      value={newName}
      onChange={(e) => setNewName(e.target.value)}
      disabled={submitting}
      required
      autoFocus
    />
  </div>
</BaseModal>
```

### 2. Form with Validation Hints (Example: NewGroupPopup)

**Use Case:** Form with input hints and validation feedback

```tsx
<BaseModal
  isOpen={true}
  onClose={onClose}
  title={t('groups:create.title')}
  error={error}
  submitButton={{
    text: submitting ? t('groups:create.submitting') : t('groups:create.submit'),
    onClick: handleSubmit,
    loading: submitting,
    disabled: submitting
  }}
>
  <div className="form-group">
    <label htmlFor="group-name">{t('groups:fields.name')} *</label>
    <input
      id="group-name"
      type="text"
      className={`form-input ${error ? 'input-error' : ''}`}
      value={groupName}
      onChange={(e) => handleNameChange(e.target.value)}
      onBlur={handleBlur}
      disabled={submitting}
    />
    <small className="input-hint">
      {t('groups:validation.nameHint')}
    </small>
  </div>
</BaseModal>
```

### 3. Warning/Danger Actions (Example: ForceConfirmPopup)

**Use Case:** Dangerous action requiring confirmation

```tsx
<BaseModal
  isOpen={true}
  onClose={onClose}
  title={t('run:forceConfirm.title')}
  error={error}
  submitButton={{
    text: submitting ? t('run:actions.confirming') : t('run:actions.forceConfirm'),
    onClick: handleForceConfirm,
    variant: 'warning', // or 'danger'
    loading: submitting,
    disabled: submitting
  }}
>
  <div style={{ marginBottom: '1.5rem' }}>
    <p><strong>{t('run:forceConfirm.warning')}</strong></p>
    {/* Warning content */}
  </div>
</BaseModal>
```

### 4. Custom Button Styling (EditProductPopup, EditStorePopup)

**Use Case:** Popups with delete/merge buttons

**Note:** For popups with additional action sections (merge, delete), keep those sections in the children. BaseModal handles the primary submit/cancel actions only.

```tsx
<BaseModal
  isOpen={true}
  onClose={onClose}
  title={t('admin:edit.product.title')}
  error={error}
  size="scrollable"
  submitButton={{
    text: submitting ? t('common:saving') : t('common:saveChanges'),
    onClick: handleUpdate,
    loading: submitting,
    disabled: submitting
  }}
>
  {/* Edit form fields */}

  <hr style={{ margin: '2rem 0', border: 'none', borderTop: '1px solid var(--color-border)' }} />

  {/* Merge Section - stays in children */}
  <div className="form-group">
    <label>{t('admin:edit.product.mergeTitle')}</label>
    {/* Merge UI */}
  </div>

  <hr style={{ margin: '2rem 0', border: 'none', borderTop: '1px solid var(--color-border)' }} />

  {/* Delete Section - stays in children */}
  <div className="form-group">
    <label style={{ color: 'var(--color-danger)' }}>{t('admin:edit.dangerZone')}</label>
    {/* Delete UI */}
  </div>
</BaseModal>
```

### 5. Modal Without Form (Example: AddProductPopup)

**Use Case:** Modal with list/search UI instead of form

```tsx
<BaseModal
  isOpen={true}
  onClose={onClose}
  title={t('product:addToRun.title')}
  error={error}
  size="md"
  asForm={false}  // Important: disable form wrapper
  cancelButton={{
    text: t('common:buttons.cancel'),
    onClick: onCancel
  }}
  customActions={
    <button onClick={() => setShowNewProductPopup(true)} className="btn btn-secondary">
      {t('product:actions.createNew')}
    </button>
  }
>
  <div className="search-container">
    <input
      type="text"
      placeholder={t('product:addToRun.searchPlaceholder')}
      value={searchTerm}
      onChange={handleSearchChange}
    />
  </div>

  <div className="products-list">
    {/* Product list */}
  </div>
</BaseModal>
```

### 6. Small Modal Size (Example: BidPopup)

**Use Case:** Compact popup for quick actions

```tsx
<BaseModal
  isOpen={true}
  onClose={onCancel}
  title={t('run:bid.title')}
  error={error}
  size="sm"  // Smaller modal
  submitButton={{
    text: currentQuantity ? t('run:actions.updateBid') : t('run:actions.placeBid'),
    onClick: handleSubmit
  }}
>
  {/* Compact form fields */}
</BaseModal>
```

---

## BaseModal Props Reference

### Required Props

| Prop | Type | Description |
|------|------|-------------|
| `isOpen` | `boolean` | Whether the modal is visible |
| `onClose` | `() => void` | Callback when modal should close |
| `children` | `ReactNode` | Modal content |

### Optional Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `string` | - | Modal title (shown in header) |
| `error` | `string` | - | Error message to display |
| `size` | `'sm' \| 'md' \| 'lg' \| 'scrollable'` | `'md'` | Modal size variant |
| `submitButton` | `BaseModalAction` | - | Submit button config |
| `cancelButton` | `BaseModalAction \| false` | Standard cancel | Cancel button config or `false` to hide |
| `customActions` | `ReactNode` | - | Additional custom action buttons |
| `className` | `string` | `''` | Additional CSS class for modal |
| `showHeader` | `boolean` | `!!title` | Show header with title |
| `asForm` | `boolean` | `true` | Render as `<form>` element |

### BaseModalAction Interface

```tsx
interface BaseModalAction {
  text: string                                           // Button text
  onClick: (e: FormEvent) => void | Promise<void>        // Click handler
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'warning'  // Button style
  loading?: boolean                                      // Loading state
  disabled?: boolean                                     // Disabled state
  type?: 'button' | 'submit'                            // Button type
}
```

---

## Remaining Popups to Migrate

### High Priority (Simple Forms)

1. **ChangePasswordPopup** - Simple, similar to ChangeNamePopup
2. **ChangeUsernamePopup** - Simple, similar to ChangeNamePopup
3. **NewRunPopup** - Form with store selection
4. **NewStorePopup** - Form with address fields
5. **CommentsPopup** - Simple text area form

### Medium Priority (Complex Forms)

6. **NewProductPopup** - Form with similar product checking, nested ConfirmDialog
7. **EditUserPopup** - Form with merge/delete sections
8. **ManageHelpersPopup** - Form with user list
9. **ReassignLeaderPopup** - Form with user selection

### Lower Priority (Special Cases)

10. **AddProductPopup** - Search UI with product list (not a form)
11. **BidPopup** - Custom keyboard handling, adjusting mode logic
12. **EditProductPopup** - Complex with merge/delete sections
13. **EditStorePopup** - Complex with merge/delete sections

---

## Edge Cases & Special Handling

### Nested Modals (NewProductPopup)

**Issue:** NewProductPopup can open ConfirmDialog

**Solution:** Keep nested modal rendering in children. BaseModal doesn't interfere with nested modals.

```tsx
<BaseModal {...props}>
  {/* Form fields */}

  {confirmState && (
    <ConfirmDialog
      message={confirmState.message}
      onConfirm={handleConfirm}
      onCancel={hideConfirm}
    />
  )}
</BaseModal>
```

### Custom Keyboard Handlers (BidPopup, AddProductPopup)

**Issue:** Some popups have custom keyboard handling (Arrow keys, Enter)

**Solution:** Add keyboard handlers to input elements, not the modal. BaseModal only handles Escape key.

```tsx
<BaseModal {...props}>
  <input
    onKeyDown={(e) => {
      if (e.key === 'Enter') {
        handleCustomEnter()
      }
      // BaseModal still handles Escape
    }}
  />
</BaseModal>
```

### Popups Without Submit Button (CommentsPopup)

**Issue:** Some popups are read-only or don't need submit

**Solution:** Omit `submitButton` prop. Only cancel button will show.

```tsx
<BaseModal
  isOpen={true}
  onClose={onClose}
  title={t('run:comments.title')}
>
  <div className="comments-list">
    {/* Read-only content */}
  </div>
</BaseModal>
```

---

## Testing After Migration

After migrating a popup, test these scenarios:

1. ✅ Modal opens and closes correctly
2. ✅ Click outside to close works
3. ✅ Escape key closes modal
4. ✅ Focus trap works (Tab cycles through focusable elements)
5. ✅ Error display shows correctly
6. ✅ Submit button shows loading state
7. ✅ Form validation still works
8. ✅ Success callback is called
9. ✅ Modal restores focus to previous element on close

---

## Tips

- **Start with simple popups** (ChangePasswordPopup, ChangeUsernamePopup)
- **Test immediately** after migration
- **Keep validation logic** exactly as-is (don't refactor during migration)
- **Preserve all accessibility attributes** (aria-labels, ids, etc.)
- **Check translation keys** are still working
- **Don't batch too many migrations** - test each one individually

---

## Questions?

- Check the three example migrations: ChangeNamePopup, NewGroupPopup, ForceConfirmPopup
- Read BaseModal.tsx component source for full API documentation
- Look at utilities.css for modal styling classes

# Shared Component Library

This document describes the reusable components available in `src/shared/components/`. **Always check here before creating new UI patterns** — if a component exists for your use case, use it to maintain consistency and reduce duplication.

---

## Table of Contents

1. [Layout Components](#layout-components)
2. [Feedback Components](#feedback-components)
3. [Data Display Components](#data-display-components)
4. [Form Components](#form-components)
5. [Navigation Components](#navigation-components)
6. [Usage Examples](#usage-examples)

---

## Quick Reference

| Need to... | Use this component |
|------------|-------------------|
| Add a page title with buttons | `<PageHeader>` |
| Show a data table | `<DataTable>` |
| Add pagination | `<Pagination>` |
| Toggle between paginated/show all | `<ShowAllToggle>` |
| Show an error message | `<ErrorAlert>` |
| Show a loading state | `<LoadingState>` |
| Display a confirmation modal | `<ConfirmDialog>` |
| Show a metric/stat | `<StatCard>` |
| Display a label + value | `<DetailField>` |
| Wrap a form input with label | `<FormField>` |
| Show paid/unpaid status | `<PaymentStatusBadge>` |
| Wide table with dual scrollbars | `<DualScrollContainer>` |

---

## Layout Components

### PageHeader

Consistent page header with title, subtitle, and action buttons.

```jsx
import { PageHeader, Button } from "../../../shared/components";

<PageHeader 
  title="Sales Records" 
  subtitle="Manage and view your book sales."
>
  <Button variant="secondary" onClick={handleExport}>Export</Button>
  <Button onClick={handleCreate}>Create New</Button>
</PageHeader>
```

**Props:**
| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `title` | string | ✅ | Main heading text |
| `subtitle` | string | | Optional description below title |
| `children` | ReactNode | | Action buttons (rendered on the right) |

---

### DualScrollContainer

Container with synchronized horizontal scrollbars at top and bottom. Use for wide tables.

```jsx
import { DualScrollContainer } from "../../../shared/components";

<DualScrollContainer contentWidth={1400}>
  <MyWideTable />
</DualScrollContainer>
```

**Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `contentWidth` | number | 1400 | Minimum width of content (sets scrollbar width) |
| `children` | ReactNode | | Content to display (usually a table) |
| `className` | string | | Additional CSS classes |

---

### Card, CardHeader, CardContent

Container for grouped content with optional header.

```jsx
import { Card, CardHeader, CardContent } from "../../../shared/components";

<Card>
  <CardHeader 
    title="Book Details" 
    subtitle="View and edit book information." 
  />
  <CardContent>
    {/* Your content here */}
  </CardContent>
</Card>
```

**Card Props:**
| Prop | Type | Description |
|------|------|-------------|
| `children` | ReactNode | Card content |
| `className` | string | Additional CSS classes |

**CardHeader Props:**
| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `title` | string | ✅ | Header title |
| `subtitle` | string | | Optional subtitle |

---

## Feedback Components

### ErrorAlert

Consistent error and warning messages.

```jsx
import { ErrorAlert } from "../../../shared/components";

// Default (red) - for errors
<ErrorAlert>Something went wrong. Please try again.</ErrorAlert>

// Warning (amber) - for non-blocking warnings
<ErrorAlert variant="warning">
  <strong>Warning:</strong> This book has existing sales records.
</ErrorAlert>

// Left border style - alternative look
<ErrorAlert variant="leftBorder">{errorMessage}</ErrorAlert>
```

**Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | ReactNode | | Error message content |
| `variant` | `"default"` \| `"warning"` \| `"leftBorder"` | `"default"` | Visual style |
| `className` | string | | Additional CSS classes |

**When to use each variant:**
- `default` — Validation errors, API failures, blocking errors
- `warning` — Non-blocking warnings, cautions, confirmations
- `leftBorder` — Alternative style, good for form validation summaries

---

### LoadingState

Spinner with loading message.

```jsx
import { LoadingState } from "../../../shared/components";

// Inline loading
<LoadingState message="Loading sales data..." />

// Full page loading
<LoadingState message="Loading..." fullPage />
```

**Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `message` | string | `"Loading..."` | Text to display |
| `fullPage` | boolean | `false` | Adds padding wrapper for page-level loading |
| `className` | string | | Additional CSS classes |

---

### ConfirmDialog

Modal dialog for confirmations. Supports both simple text and complex JSX content.

```jsx
import { ConfirmDialog, ErrorAlert } from "../../../shared/components";

// Simple usage (string body)
<ConfirmDialog
  open={isOpen}
  title="Mark as Paid?"
  body="This will mark all unpaid royalties for this author as paid."
  confirmText="Confirm"
  confirming={isProcessing}
  onCancel={() => setIsOpen(false)}
  onConfirm={handleConfirm}
/>

// Complex usage (JSX children) - for delete confirmations, etc.
<ConfirmDialog
  open={isOpen}
  title="Delete Book?"
  confirmText="Delete"
  confirmVariant="danger"
  confirming={isDeleting}
  onCancel={handleCancel}
  onConfirm={handleDelete}
>
  <div className="space-y-3">
    <ErrorAlert>This action cannot be undone.</ErrorAlert>
    <p>Are you sure you want to delete "{book.title}"?</p>
  </div>
</ConfirmDialog>
```

**Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `open` | boolean | | Whether dialog is visible |
| `title` | string | | Dialog title |
| `body` | string | | Simple text content (ignored if `children` provided) |
| `children` | ReactNode | | Complex JSX content (takes precedence over `body`) |
| `confirmText` | string | `"Confirm"` | Confirm button label |
| `confirmVariant` | `"primary"` \| `"danger"` | `"primary"` | Confirm button style |
| `confirming` | boolean | `false` | Loading state (disables buttons, shows "...") |
| `onCancel` | function | | Cancel handler |
| `onConfirm` | function | | Confirm handler |

---

## Data Display Components

### DataTable

Full-featured data table with sorting, loading states, and action buttons.

```jsx
import { DataTable } from "../../../shared/components";

const columns = [
  {
    label: "Title",
    sortKey: "title",  // enables sorting
    render: (row) => <span className="font-medium">{row.title}</span>,
  },
  {
    label: "Author",
    render: (row) => row.author_name,
  },
  {
    label: "Revenue",
    className: "text-right",
    render: (row) => `$${row.revenue}`,
  },
  {
    label: "Actions",
    type: "actions",
    getActions: (row) => [
      { label: "Edit", to: `/books/${row.id}`, variant: "secondary" },
      { label: "Delete", onClick: () => handleDelete(row), variant: "danger" },
    ],
  },
];

<DataTable
  data={books}
  columns={columns}
  loading={isLoading}
  ordering={currentOrdering}
  onSort={handleSort}
  onRowClick={(row) => navigate(`/books/${row.id}`)}
  emptyMessage="No books found."
  loadingMessage="Loading books..."
/>
```

**Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | array | | Array of row objects (must have `id` property) |
| `columns` | array | | Column definitions (see below) |
| `loading` | boolean | `false` | Shows loading spinner |
| `ordering` | string | | Current sort field (prefix with `-` for desc) |
| `onSort` | function | | Sort handler `(field) => void` |
| `onRowClick` | function | | Row click handler `(row) => void` |
| `emptyMessage` | string | `"No data found."` | Message when data is empty |
| `loadingMessage` | string | `"Loading data..."` | Message while loading |

**Column Definition:**
| Property | Type | Description |
|----------|------|-------------|
| `label` | string | Column header text |
| `sortKey` | string | Field name for sorting (omit to disable sorting) |
| `className` | string | CSS classes for the column (e.g., `"text-right"`) |
| `render` | function | `(row) => ReactNode` — how to render the cell |
| `type` | `"actions"` | Special column type for action buttons |
| `getActions` | function | `(row) => Action[]` — returns action button configs |

**Action Definition:**
| Property | Type | Description |
|----------|------|-------------|
| `label` | string | Button text |
| `to` | string | Link URL (renders as Link) |
| `onClick` | function | Click handler (renders as Button) |
| `variant` | string | Button variant (`"primary"`, `"secondary"`, `"danger"`) |

---

### Pagination

Page navigation controls.

```jsx
import { Pagination } from "../../../shared/components";

<Pagination
  page={currentPage}
  totalPages={totalPages}
  onPrev={() => setPage(p => Math.max(1, p - 1))}
  onNext={() => setPage(p => Math.min(totalPages, p + 1))}
/>
```

**Props:**
| Prop | Type | Description |
|------|------|-------------|
| `page` | number | Current page number |
| `totalPages` | number | Total number of pages |
| `onPrev` | function | Previous button handler |
| `onNext` | function | Next button handler |

---

### ShowAllToggle

Toggle between paginated and "show all" views.

```jsx
import { ShowAllToggle } from "../../../shared/components";

<ShowAllToggle
  showAll={showAll}
  onToggle={() => {
    setShowAll(v => !v);
    setPage(1);  // Reset to page 1 when toggling
  }}
/>
```

**Props:**
| Prop | Type | Description |
|------|------|-------------|
| `showAll` | boolean | Current state |
| `onToggle` | function | Toggle handler |
| `className` | string | Additional CSS classes |

---

### StatCard

Metric display card with color variants.

```jsx
import { StatCard } from "../../../shared/components";

<div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
  <StatCard
    label="Publisher Revenue"
    value="$12,345.67"
    loading={isLoading}
  />
  <StatCard
    label="Total Royalties"
    value="$1,234.56"
    loading={isLoading}
  />
  <StatCard
    label="Paid Royalties"
    value="$1,000.00"
    loading={isLoading}
    variant="success"
  />
  <StatCard
    label="Unpaid Royalties"
    value="$234.56"
    loading={isLoading}
    variant="danger"
  />
</div>
```

**Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `label` | string | | Metric label (displayed uppercase) |
| `value` | string \| number | | Metric value |
| `loading` | boolean | `false` | Shows "Loading…" instead of value |
| `variant` | `"default"` \| `"success"` \| `"danger"` | `"default"` | Color scheme |
| `className` | string | | Additional CSS classes |

---

### DetailField

Read-only label + value display for detail views.

```jsx
import { DetailField } from "../../../shared/components";

<DetailField label="Title">{book.title}</DetailField>

<DetailField label="ISBN-13">
  <span className="font-mono">{book.isbn_13}</span>
</DetailField>

// Automatically shows "—" when empty
<DetailField label="ISBN-10">{book.isbn_10}</DetailField>
```

**Props:**
| Prop | Type | Description |
|------|------|-------------|
| `label` | string | Field label (displayed uppercase) |
| `children` | ReactNode | Field value (shows "—" if empty) |
| `className` | string | Additional CSS classes |

---

### PaymentStatusBadge

Consistent paid/unpaid status indicators.

```jsx
import { PaymentStatusBadge } from "../../../shared/components";

// Full badge with label
<PaymentStatusBadge status="paid" />      // Green: "Paid"
<PaymentStatusBadge status="unpaid" />    // Red: "Unpaid"
<PaymentStatusBadge status="partial" />   // Amber: "Partially Paid"
<PaymentStatusBadge status="success" />   // Green: "Fully Paid"

// Dot only (for compact/inline use)
<PaymentStatusBadge status="paid" variant="dot" />
```

**Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `status` | `"paid"` \| `"unpaid"` \| `"partial"` \| `"success"` \| `"danger"` \| `"warning"` | | Status type |
| `variant` | `"badge"` \| `"dot"` | `"badge"` | Display style |
| `className` | string | | Additional CSS classes |

---

## Form Components

### Button

Standard button with variants.

```jsx
import { Button } from "../../../shared/components";

<Button>Primary Action</Button>
<Button variant="secondary">Cancel</Button>
<Button variant="danger">Delete</Button>
<Button disabled={isSubmitting}>
  {isSubmitting ? "Saving..." : "Save"}
</Button>
```

**Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | ReactNode | | Button content |
| `variant` | `"primary"` \| `"secondary"` \| `"danger"` | `"primary"` | Button style |
| `disabled` | boolean | | Disabled state |
| `className` | string | | Additional CSS classes |
| `...props` | | | All standard button props (onClick, type, etc.) |

---

### Input

Styled text input.

```jsx
import { Input } from "../../../shared/components";

<Input
  value={title}
  onChange={(e) => setTitle(e.target.value)}
  placeholder="Enter book title..."
  required
/>

// With custom className
<Input className="font-mono" value={isbn} onChange={...} />
```

**Props:**
| Prop | Type | Description |
|------|------|-------------|
| `...props` | | All standard input props (value, onChange, placeholder, etc.) |
| `className` | string | Additional CSS classes (merged with base styles) |

---

### FormField

Wrapper for form inputs with label.

```jsx
import { FormField, Input } from "../../../shared/components";

<FormField label="Book Title">
  <Input value={title} onChange={(e) => setTitle(e.target.value)} required />
</FormField>

<FormField label="ISBN-13" htmlFor="isbn13">
  <Input id="isbn13" value={isbn13} onChange={...} />
</FormField>
```

**Props:**
| Prop | Type | Description |
|------|------|-------------|
| `label` | string | Label text |
| `htmlFor` | string | Associates label with input (for accessibility) |
| `children` | ReactNode | Form input(s) |
| `className` | string | Additional CSS classes |

---

### MonthPicker

Month/year date picker with browser fallback.

```jsx
import { MonthPicker } from "../../../shared/components";

<MonthPicker
  label="Publication Date"
  value={publicationMonth}        // "YYYY-MM" format
  onChange={setPublicationMonth}  // receives "YYYY-MM" string
  min="2000-01"                   // optional minimum date
  required
/>
```

**Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `label` | string | | Label text |
| `value` | string | | Value in "YYYY-MM" format |
| `onChange` | function | | Change handler, receives "YYYY-MM" string |
| `min` | string | | Minimum date in "YYYY-MM" format |
| `required` | boolean | `false` | Whether field is required |
| `name` | string | | Input name attribute |
| `className` | string | | Additional CSS classes |

---

### Spinner

Simple loading spinner.

```jsx
import { Spinner } from "../../../shared/components";

<Spinner />

// Typically used with text
<div className="flex items-center gap-2">
  <Spinner />
  <span>Loading...</span>
</div>
```

*Note: Prefer `<LoadingState>` for most use cases as it includes the text.*

---

## Navigation Components

### Navbar

Application navigation bar. Usually rendered once at the app root.

```jsx
import { Navbar } from "../../../shared/components";

<Navbar />
```

---

## Usage Examples

### List Page Pattern

```jsx
import {
  PageHeader,
  Button,
  Card,
  CardContent,
  DataTable,
  Pagination,
  ShowAllToggle,
  DualScrollContainer,
  LoadingState,
} from "../../../shared/components";

export default function BooksListPage() {
  const { data, loading, page, totalPages, setPage, showAll, toggleShowAll } = useBooksList();

  return (
    <div className="p-6 max-w-full">
      <PageHeader title="Books" subtitle="Manage your book catalog.">
        <Button onClick={() => navigate("/books/create")}>Create Book</Button>
      </PageHeader>

      <Card>
        <CardContent>
          <div className="flex justify-between items-center mb-4">
            <span>{data.length} books</span>
            <ShowAllToggle showAll={showAll} onToggle={toggleShowAll} />
          </div>

          <DualScrollContainer contentWidth={1400}>
            <DataTable
              data={data}
              columns={columns}
              loading={loading}
              emptyMessage="No books found."
            />
          </DualScrollContainer>

          {!showAll && (
            <div className="mt-4">
              <Pagination
                page={page}
                totalPages={totalPages}
                onPrev={() => setPage(p => p - 1)}
                onNext={() => setPage(p => p + 1)}
              />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
```

### Detail Page Pattern

```jsx
import {
  Card,
  CardHeader,
  CardContent,
  Button,
  DetailField,
  StatCard,
  ErrorAlert,
  ConfirmDialog,
} from "../../../shared/components";

export default function BookDetailPage() {
  const { book, loading, error } = useBook(bookId);
  const [deleteOpen, setDeleteOpen] = useState(false);

  if (loading) return <LoadingState message="Loading book..." fullPage />;
  if (error) return <ErrorAlert>{error}</ErrorAlert>;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <Card>
        <CardHeader title="Book Details" subtitle="View book information." />
        <CardContent>
          <div className="flex gap-2 mb-6">
            <Button variant="secondary" onClick={() => setEditing(true)}>Edit</Button>
            <Button variant="danger" onClick={() => setDeleteOpen(true)}>Delete</Button>
          </div>

          <div className="space-y-4">
            <DetailField label="Title">{book.title}</DetailField>
            <DetailField label="ISBN-13">
              <span className="font-mono">{book.isbn_13}</span>
            </DetailField>
          </div>
        </CardContent>
      </Card>

      {/* Stats Section */}
      <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Total Sales" value={book.total_sales} />
        <StatCard label="Revenue" value={`$${book.revenue}`} />
        <StatCard label="Paid" value={`$${book.paid}`} variant="success" />
        <StatCard label="Unpaid" value={`$${book.unpaid}`} variant="danger" />
      </div>

      <ConfirmDialog
        open={deleteOpen}
        title="Delete Book?"
        confirmText="Delete"
        confirmVariant="danger"
        onCancel={() => setDeleteOpen(false)}
        onConfirm={handleDelete}
      >
        <ErrorAlert>This action cannot be undone.</ErrorAlert>
      </ConfirmDialog>
    </div>
  );
}
```

### Form Page Pattern

```jsx
import {
  Card,
  CardHeader,
  CardContent,
  Button,
  Input,
  FormField,
  MonthPicker,
  ErrorAlert,
} from "../../../shared/components";

export default function CreateBookPage() {
  const [title, setTitle] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <Card>
        <CardHeader title="Create Book" subtitle="Add a new book to the catalog." />
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-5">
            <FormField label="Title">
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </FormField>

            <MonthPicker
              label="Publication Date"
              value={publicationMonth}
              onChange={setPublicationMonth}
              required
            />

            {error && <ErrorAlert>{error}</ErrorAlert>}

            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => navigate(-1)}>
                Cancel
              </Button>
              <Button disabled={submitting}>
                {submitting ? "Creating..." : "Create"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

---

## Adding New Components

Before creating a new component:

1. **Check this document** — the component may already exist
2. **Check if an existing component can be extended** — add a variant or prop
3. **If truly new**, add it to `src/shared/components/` and update this README

New shared components should:
- Accept a `className` prop for customization
- Use Tailwind utility classes
- Be exported from `src/shared/components/index.js`
- Be documented in this README with props table and examples

/**
 * Table: a semantic data table that collapses to labelled cards on narrow
 * screens. The markup stays a real `<table>` with `<caption>` and column
 * headers (so header→value association survives for screen readers); the
 * mobile card layout is pure CSS driven by each cell's `data-label`.
 */
import type { ReactNode } from 'react'
import styles from './Table.module.css'

export interface TableColumn {
  key: string
  header: string
}

export interface TableRow {
  key: string
  cells: Record<string, ReactNode>
}

export interface TableProps {
  caption: string
  columns: TableColumn[]
  rows: TableRow[]
}

export function Table({ caption, columns, rows }: TableProps) {
  return (
    <table className={styles.table}>
      <caption>{caption}</caption>
      <thead>
        <tr>
          {columns.map((column) => (
            <th key={column.key} scope="col">
              {column.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.key}>
            {columns.map((column) => (
              <td key={column.key} data-label={column.header}>
                {row.cells[column.key]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}

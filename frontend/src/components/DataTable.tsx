import type { ReactNode } from "react";

export type Column<T> = {
  key: keyof T;
  header: string;
  render?: (value: T[keyof T], item: T) => ReactNode;
};

type DataTableProps<T> = {
  data: T[];
  columns: Column<T>[];
  keyExtractor: (item: T) => string | number;
  onRowClick?: (item: T) => void;
};

export function DataTable<T>({
  data,
  columns,
  keyExtractor,
  onRowClick,
}: DataTableProps<T>) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800/80">
            {columns.map((col) => (
              <th
                key={String(col.key)}
                className="px-4 py-3 font-semibold text-slate-600 dark:text-slate-300"
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-8 text-center text-slate-400 dark:text-slate-500"
              >
                No data found
              </td>
            </tr>
          ) : (
            data.map((item) => (
              <tr
                key={keyExtractor(item)}
                onClick={() => onRowClick?.(item)}
                className={`border-b border-slate-100 transition-colors even:bg-slate-50/50 hover:bg-mint-100/50 dark:border-slate-700/50 dark:even:bg-slate-800/30 dark:hover:bg-navy-800/30 ${
                  onRowClick ? "cursor-pointer" : ""
                }`}
              >
                {columns.map((col) => (
                  <td key={String(col.key)} className="px-4 py-3 text-slate-700 dark:text-slate-200">
                    {col.render
                      ? col.render(item[col.key], item)
                      : String(item[col.key] ?? "")}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

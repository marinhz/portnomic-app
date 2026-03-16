import { useState, useRef, useEffect } from "react";
import { ChevronDown } from "lucide-react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export type SearchableOption = {
  id: string;
  label: string;
};

type SearchableSelectProps = {
  value: string;
  onSelect: (id: string) => void;
  options: SearchableOption[];
  onSearch?: (query: string) => void;
  searchPlaceholder?: string;
  loading?: boolean;
  required?: boolean;
  disabled?: boolean;
  className?: string;
  "aria-label"?: string;
  /** When "server", options are from API search - no client filter. Default "client". */
  filterMode?: "client" | "server";
};

export function SearchableSelect({
  value,
  onSelect,
  options,
  onSearch,
  searchPlaceholder = "Search...",
  loading = false,
  required = false,
  disabled = false,
  className,
  "aria-label": ariaLabel,
  filterMode = "client",
}: SearchableSelectProps) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedOption = options.find((o) => o.id === value);
  const displayValue = selectedOption?.label ?? "";
  const showInput = open || !value;
  const inputValue = open ? query : displayValue;

  const filtered =
    filterMode === "server"
      ? options
      : query.trim() === ""
        ? options
        : options.filter((o) =>
            o.label.toLowerCase().includes(query.toLowerCase()),
          );

  useEffect(() => {
    if (open && onSearch) {
      onSearch(query);
    }
  }, [open, query, onSearch]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      <div className="relative">
        <input
          type="text"
          value={inputValue}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={() => {
            setOpen(true);
            setQuery("");
          }}
          placeholder={searchPlaceholder}
          required={required && !value}
          disabled={disabled}
          aria-label={ariaLabel}
          aria-expanded={open}
          aria-haspopup="listbox"
          aria-autocomplete="list"
          className="h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-base shadow-xs transition-[color,box-shadow] outline-none selection:bg-primary selection:text-primary-foreground placeholder:text-muted-foreground disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 md:text-sm dark:bg-input/30 focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 pr-9"
        />
        <ChevronDown
          className="pointer-events-none absolute right-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden
        />
      </div>

      {open && (
        <ul
          role="listbox"
          className="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-md border bg-popover py-1 text-popover-foreground shadow-md"
        >
          {loading ? (
            <li className="px-3 py-2 text-sm text-muted-foreground">
              Loading...
            </li>
          ) : filtered.length === 0 ? (
            <li className="px-3 py-2 text-sm text-muted-foreground">
              No results
            </li>
          ) : (
            filtered.map((opt) => (
              <li
                key={opt.id}
                role="option"
                aria-selected={opt.id === value}
                className={cn(
                  "cursor-pointer px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground",
                  opt.id === value && "bg-accent",
                )}
                onClick={() => {
                  onSelect(opt.id);
                  setOpen(false);
                  setQuery("");
                }}
              >
                {opt.label}
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}

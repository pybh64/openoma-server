import { useState, useCallback, useEffect, useRef } from "react";
import { useQuery, useMutation, type AnyVariables, type DocumentInput } from "urql";

interface UseEntityListOptions {
  query: DocumentInput<unknown, AnyVariables>;
  queryKey: string;
  limit?: number;
  debounceMs?: number;
}

export function useEntityList<T>({
  query,
  queryKey,
  limit = 50,
  debounceMs = 300,
}: UseEntityListOptions) {
  const [offset, setOffset] = useState(0);
  const [nameFilter, setNameFilter] = useState<string | undefined>(undefined);
  const [debouncedFilter, setDebouncedFilter] = useState<string | undefined>(undefined);
  const timerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setDebouncedFilter(nameFilter || undefined);
      setOffset(0);
    }, debounceMs);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [nameFilter, debounceMs]);

  const [result, reexecute] = useQuery({
    query,
    variables: {
      nameFilter: debouncedFilter,
      limit,
      offset,
      latestOnly: true,
    },
  });

  const data: T[] = (result.data as Record<string, T[]> | undefined)?.[queryKey] ?? [];
  const loading = result.fetching;
  const error = result.error;
  const hasMore = data.length === limit;

  const refresh = useCallback(() => {
    reexecute({ requestPolicy: "network-only" });
  }, [reexecute]);

  return {
    data,
    loading,
    error,
    hasMore,
    offset,
    limit,
    setOffset,
    nameFilter,
    setNameFilter,
    refresh,
  };
}

interface UseDeleteEntityOptions {
  mutation: DocumentInput<unknown, AnyVariables>;
  onSuccess?: () => void;
}

export function useDeleteEntity({ mutation, onSuccess }: UseDeleteEntityOptions) {
  const [, executeMutation] = useMutation(mutation);
  const [deleting, setDeleting] = useState(false);

  const deleteEntity = useCallback(
    async (id: string, version?: number) => {
      setDeleting(true);
      try {
        const result = await executeMutation({ id, version });
        if (!result.error) onSuccess?.();
        return result;
      } finally {
        setDeleting(false);
      }
    },
    [executeMutation, onSuccess]
  );

  return { deleteEntity, deleting };
}

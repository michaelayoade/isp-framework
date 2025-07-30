import { useMutation, useQueryClient } from '@tanstack/react-query';

interface OptimisticMutationOptions<TData, TVariables, TContext> {
  mutationFn: (variables: TVariables) => Promise<TData>;
  queryKey: unknown[];
  updateFn?: (oldData: TData | undefined, variables: TVariables) => TData;
  rollbackFn?: (context: TContext | undefined) => void;
  onSuccess?: (data: TData, variables: TVariables, context: TContext) => void;
  onError?: (error: unknown, variables: TVariables, context: TContext | undefined) => void;
}

export function useOptimisticMutation<TData, TVariables, TContext = unknown>(
  options: OptimisticMutationOptions<TData, TVariables, TContext>
) {
  const queryClient = useQueryClient();
  
  const mutation = useMutation<TData, unknown, TVariables, TContext>({
    mutationFn: options.mutationFn,
    onMutate: async (variables) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: options.queryKey });
      
      // Snapshot the previous value
      const previousData = queryClient.getQueryData<TData>(options.queryKey);
      
      // Optimistically update to the new value
      if (options.updateFn) {
        queryClient.setQueryData<TData>(options.queryKey, (old) => 
          options.updateFn ? options.updateFn(old, variables) : old
        );
      }
      
      // Return a context object with the snapshotted value
      return { previousData } as unknown as TContext;
    },
    onError: (error, variables, context) => {
      // Rollback to the previous value
      queryClient.setQueryData(options.queryKey, (context as { previousData: TData }).previousData);
      
      // Call custom error handler if provided
      if (options.onError) {
        options.onError(error, variables, context);
      }
    },
    onSuccess: (data, variables, context) => {
      // Call custom success handler if provided
      if (options.onSuccess) {
        options.onSuccess(data, variables, context);
      }
    },
    onSettled: () => {
      // Refetch the data to ensure consistency
      queryClient.invalidateQueries({ queryKey: options.queryKey });
    },
  });
  
  return mutation;
}

// Helper function to update paginated data
export function updatePaginatedData<T>(
  oldData: { items: T[]; total: number } | undefined,
  newItem: T,
  action: 'add' | 'update' | 'remove',
  idField: keyof T
) {
  if (!oldData) return oldData;
  
  const items = [...oldData.items];
  
  switch (action) {
    case 'add':
      return {
        ...oldData,
        items: [newItem, ...items],
        total: oldData.total + 1,
      };
    case 'update':
      const index = items.findIndex(item => item[idField] === newItem[idField]);
      if (index !== -1) {
        items[index] = newItem;
      }
      return {
        ...oldData,
        items,
      };
    case 'remove':
      return {
        ...oldData,
        items: items.filter(item => item[idField] !== newItem[idField]),
        total: oldData.total - 1,
      };
    default:
      return oldData;
  }
}

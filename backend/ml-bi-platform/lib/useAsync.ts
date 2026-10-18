import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError } from '@/lib/api';

type AsyncState<T> = {
  data: T | null;
  error: string;
  loading: boolean;
};

export function useAsync<T>(
  loader: () => Promise<T>,
  deps: unknown[],
): AsyncState<T> & { reload: () => void } {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    error: '',
    loading: true,
  });
  const [nonce, setNonce] = useState(0);
  const loaderRef = useRef(loader);
  loaderRef.current = loader;

  useEffect(() => {
    let cancelled = false;

    setState((previous) => ({ ...previous, loading: true, error: '' }));

    loaderRef
      .current()
      .then((data) => {
        if (!cancelled) setState({ data, error: '', loading: false });
      })
      .catch((error: unknown) => {
        if (cancelled) return;

        setState({
          data: null,
          error:
            error instanceof ApiError
              ? error.message
              : 'Something went wrong while loading data.',
          loading: false,
        });
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nonce, ...deps]);

  const reload = useCallback(() => setNonce((value) => value + 1), []);

  return { ...state, reload };
}

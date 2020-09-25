import React from "react";

export function useAsyncError() {
  // eslint-disable-next-line
  const [_error, setError] = React.useState();

  return React.useCallback(
    (err) => {
      setError(() => {
        throw err;
      });
    },
    [setError]
  );
}

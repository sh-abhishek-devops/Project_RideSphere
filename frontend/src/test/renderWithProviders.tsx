import type { ReactElement, ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

interface RenderOptions {
  route?: string;
  wrapper?: ({ children }: { children: ReactNode }) => ReactElement;
}

export function renderWithProviders(ui: ReactElement, options: RenderOptions = {}) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false
      },
      mutations: {
        retry: false
      }
    }
  });

  function Providers({ children }: { children: ReactNode }) {
    const content = (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[options.route ?? "/"]}>{children}</MemoryRouter>
      </QueryClientProvider>
    );

    return options.wrapper ? options.wrapper({ children: content }) : content;
  }

  return {
    queryClient,
    ...render(ui, { wrapper: Providers })
  };
}

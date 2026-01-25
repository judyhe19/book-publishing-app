import React from "react";
import { Providers } from "./providers";
import { AppRoutes } from "./routes";

export default function App() {
  return (
    <Providers>
      <AppRoutes />
    </Providers>
  );
}
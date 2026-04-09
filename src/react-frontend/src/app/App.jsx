import React from "react";
import { useEffect, useState } from "react";
import { Providers } from "./providers";
import { AppRoutes } from "./routes";
import { getBranding } from "../shared/api/brandingApi";

export default function App() {
  const [branding, setBranding] = useState(null);
  useEffect(() => {
    async function loadBranding() {
      try {
        const data = await getBranding();
        setBranding(data);

        // set page title
        if (data?.app_title) {
          document.title = data.app_title;
        }

        // set favicon
        if (data?.publisher_favicon_url) {
          let link = document.querySelector("link[rel='icon']");

          if (!link) {
            link = document.createElement("link");
            link.rel = "icon";
            document.head.appendChild(link);
          }

          link.type = "image/png";
          link.href = data.publisher_favicon_url;
        }
      } catch (e) {
        console.error("Failed to load branding:", e);
      }
    }

    loadBranding();
  }, []);

  return (
    <Providers branding={branding}>
      <AppRoutes />
    </Providers>
  );
}
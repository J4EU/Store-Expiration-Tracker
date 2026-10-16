import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// 배포 Nginx의 `location = /api { return 308 /api/; }`와 같이 /api 자체 요청을 /api/로 정규화한다.
function apiTrailingSlashRedirect() {
  return {
    name: "api-trailing-slash-redirect",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const pathname = req.url.split("?")[0];
        if (pathname !== "/api") {
          next();
          return;
        }

        res.statusCode = 308;
        res.setHeader("Location", "/api/");
        res.end();
      });
    },
  };
}

export default defineConfig({
  plugins: [vue(), apiTrailingSlashRedirect()],
  server: {
    port: 5173,
    proxy: {
      // 배포 Nginx의 `location /api/`와 같은 경계로 /api/... 요청만 backend로 전달한다.
      "/api/": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\//, "/"),
      },
    },
  },
});

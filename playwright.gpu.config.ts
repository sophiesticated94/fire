import {defineConfig} from '@playwright/test';
const port=Number(process.env.GPU_TEST_PORT??5174);
export default defineConfig({testDir:'tests/gpu',testMatch:'*.spec.ts',timeout:120000,workers:1,use:{baseURL:`http://127.0.0.1:${port}`,headless:true,channel:'msedge',launchOptions:{args:['--use-angle=d3d11']}},webServer:{command:`npm run dev -- --port ${port} --strictPort --mode gputest`,url:`http://127.0.0.1:${port}/tests/gpu/harness.html`,reuseExistingServer:false,timeout:30000}});

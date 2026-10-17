import {defineConfig} from '@playwright/test';
const port=Number(process.env.GPU_TEST_PORT??5174);
const args=['--use-angle=d3d11'];
if(process.env.IGNIS_GPU_ADAPTER==='rtx')args.push('--force-high-performance-gpu','--use-webgpu-power-preference=force-high-performance','--enable-webgpu-developer-features');
export default defineConfig({testDir:'tests/gpu',outputDir:`test-results/gpu-${port}`,testMatch:'*.spec.ts',timeout:120000,workers:1,use:{baseURL:`http://127.0.0.1:${port}`,headless:true,channel:'msedge',launchOptions:{args}},webServer:{command:`npm run dev -- --port ${port} --strictPort --mode gputest`,url:`http://127.0.0.1:${port}/tests/gpu/harness.html`,reuseExistingServer:false,timeout:30000}});

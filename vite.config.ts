import { defineConfig } from 'vite';
export default defineConfig(({mode})=>({server:{hmr:mode==='gputest'?false:undefined,proxy:{'/api':'http://127.0.0.1:8765'}}}));

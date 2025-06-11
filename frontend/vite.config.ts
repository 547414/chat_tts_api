import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path';
import Components from 'unplugin-vue-components/vite';
import {VantResolver} from 'unplugin-vue-components/resolvers';
import AutoImport from 'unplugin-auto-import/vite';

export default defineConfig(({mode}) => {
    let outDir = 'dist/production';

    if (mode === 'development') {
        outDir = 'dist/development';
    } else if (mode === 'test') {
        outDir = 'dist/test';
    } else if (mode === 'production') {
        outDir = 'dist/production';
    }

    return {
        plugins: [
            vue(),
            Components({
                resolvers: [VantResolver()],
            }),
            AutoImport({
                resolvers: [VantResolver()],
            }),
        ],
        resolve: {
            alias: {
                '@': path.resolve(__dirname, './src'),
            }
        },
        build: {
            outDir,
        },
    }
})

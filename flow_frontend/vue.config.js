const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    port: 8082,
    proxy: {
      '/api': {
        target: 'http://localhost:8002', // 更正 Django 后端运行地址
        changeOrigin: true,
        // pathRewrite: { '^/api': '' }, // 如果后端 API 不包含 /api 前缀，则取消注释此行
      }
    }
  },
  chainWebpack: config => {
    config
      .plugin('html')
      .tap(args => {
        args[0].title = "王老吉流向客户系统";
        return args;
      });
  }
})

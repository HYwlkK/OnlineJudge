# QDUOJ 原界面中的错题本

本目录保存对 **OnlineJudgeFE `oj_2.7.5`** 的 Vue 源码修改。`Dockerfile` 下载同版本源码，校验 SHA-256，将本目录的源码覆盖进去，再编译前台和后台。

错题本使用原 OJ 的导航栏、登录状态、`router-view`、Panel、Table 和 Page。导航位置在“题目”之后，路径为 `/wrong-problems`。点击题目进入原题目页面，点击最近失败结果进入原提交详情。

## 源码对应关系

| 文件 | 作用 |
| --- | --- |
| `src/pages/oj/components/NavBar.vue` | 原导航栏增加“错题本”菜单 |
| `src/pages/oj/router/routes.js` | 增加需要登录的 Vue 路由 |
| `src/pages/oj/api.js` | 调用本人错题接口 |
| `src/pages/oj/views/problem/WrongProblemList.vue` | 错题列表、空状态、分页、刷新和原题入口 |
| `config/dev.env.js` | 源码压缩包无 `.git` 时提供构建版本 |
| `prepare.js` | 应用源文件；将旧压缩器并发限制为 2，适配重复构建时的文件清理，并在成功写完构建产物后结束旧 Webpack 进程 |

其余 Vue 文件和依赖版本沿用该上游发布版及其 `package-lock.json`。原项目采用 MIT 许可证，见本目录 `LICENSE`。

## 单独构建前端

使用 Node.js 22.14，在下载并解压的 `OnlineJudgeFE-oj_2.7.5` 源码目录运行：

```sh
node /path/to/OnlineJudge-master/frontend/prepare.js .
npm ci --legacy-peer-deps --ignore-scripts --no-audit --no-fund
export NODE_OPTIONS=--openssl-legacy-provider
NODE_ENV=production npm run build:dll
npm run build
```

输出在该源码目录的 `dist`，项目 Docker 构建会自动完成上述步骤。`--openssl-legacy-provider` 用于旧 Webpack 3 的构建哈希，与浏览器里的登录和判题无关。

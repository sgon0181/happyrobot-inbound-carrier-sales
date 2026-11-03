const fs = require('node:fs');
const path = require('node:path');
const ts = require('typescript');
module.exports = function loadTs(relative, overrides = {}, cache = new Map()) {
  const file = path.resolve(relative);
  if (cache.has(file)) return cache.get(file).exports;
  const { outputText } = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true },
  });
  const loaded = { exports: {} };
  cache.set(file, loaded);
  const localRequire = (name) => {
    if (Object.hasOwn(overrides, name)) return overrides[name];
    if (!name.startsWith('@/')) return require(name);
    const target = `src/${name.slice(2)}`;
    const suffix = fs.existsSync(`${target}.ts`) ? '.ts' : '.tsx';
    return module.exports(target + suffix, overrides, cache);
  };
  new Function('module', 'exports', 'require', outputText)(loaded, loaded.exports, localRequire);
  return loaded.exports;
};

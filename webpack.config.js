/*eslint-env node*/
/*eslint import/no-nodejs-modules:0 */
const path = require('path');
const webpack = require('webpack');
const babelConfig = require('./babel.config');
const CompressionPlugin = require('compression-webpack-plugin');
const LodashModuleReplacementPlugin = require('lodash-webpack-plugin');

const APPS = [];

const IS_PRODUCTION = process.env.NODE_ENV === 'production';
const WEBPACK_MODE = IS_PRODUCTION ? 'production' : 'development';

function getConfig(app) {
  const pyName = app.replace('-', '_');
  const staticPrefix = `src/sentry_plugins/${pyName}/static/${pyName}`;
  const distPath = `${staticPrefix}/dist`;

  const config = {
    mode: WEBPACK_MODE,
    name: app,
    entry: `./${pyName}.jsx`,
    context: path.join(__dirname, staticPrefix),
    externals: {
      react: 'React',
      'react-dom': 'ReactDOM',
      'react-router': 'Router',
      reflux: 'Reflux',
      moment: 'moment',
      sentry: 'SentryApp',
      'prop-types': 'PropTypes'
    },
    module: {
      rules: [
        {
          test: /\.jsx?$/,
          include: path.join(__dirname, staticPrefix),
          exclude: /(vendor|node_modules)/,
          use: [
            {
              loader: 'babel-loader',
              // Disable loading the configFile for when plugins are being
              // built by a webpack devserver *outside* of this directory.
              // Otherwise the loader will try and locate the babel.config.js
              // file, which will be sentry or getsentrys.
              options: {...babelConfig, configFile: false}
            }
          ]
        }
      ]
    },
    plugins: [new LodashModuleReplacementPlugin()],
    resolve: {
      extensions: ['*', '.jsx', '.js']
    },
    output: {
      path: path.join(__dirname, distPath),
      filename: `${app}.js`,
      sourceMapFilename: `${app}.js.map`
    },
    devtool: IS_PRODUCTION ? 'source-map' : 'cheap-module-eval-source-map'
  };

  // This compression-webpack-plugin generates pre-compressed files
  // ending in .gz, to be picked up and served by our internal static media
  // server as well as nginx when paired with the gzip_static module.
  if (IS_PRODUCTION) {
    config.plugins.push(
      new CompressionPlugin({
        algorithm: 'gzip',
        test: /\.(js|map|css|svg|html|txt|ico|eot|ttf)$/
      })
    );
  }

  return config;
}

module.exports = APPS.map(getConfig);

/*eslint-env node*/
/*eslint no-var:0*/
var path = require('path'),
    webpack = require('webpack');

var APPS = [
  'hipchat-ac',
  'jira'
];

var IS_PRODUCTION = process.env.NODE_ENV === 'production';

function getConfig(app) {
  var pyName = app.replace('-', '_');
  var staticPrefix = 'src/sentry_plugins/' + pyName + '/static/' + pyName,
      distPath = staticPrefix + '/dist';

  var config = {
    context: path.join(__dirname, staticPrefix),
    externals: {
      'react': 'React',
      'react-dom': 'ReactDOM',
      'react-router': 'Router',
      'reflux': 'Reflux',
      'moment': 'moment',
      'sentry': 'Sentry',
      'underscore': 'underscore'
    },
    name: app,
    entry: pyName,
    module: {
      loaders: [
        {
          test: /\.jsx?$/,
          loader: 'babel-loader',
          include: path.join(__dirname, staticPrefix),
          exclude: /(vendor|node_modules)/
        }
      ]
    },
    plugins: [
      new webpack.optimize.DedupePlugin()
    ],
    resolve: {
      modulesDirectories: [staticPrefix, 'node_modules'],
      extensions: ['', '.jsx', '.js']
    },
    root: __dirname,
    output: {
      path: path.join(__dirname, distPath),
      filename: app + '.js',
      sourceMapFilename: app + '.js.map',
    },
    devtool: IS_PRODUCTION ?
      '#source-map' :
      '#cheap-module-eval-source-map'
  };


  // This compression-webpack-plugin generates pre-compressed files
  // ending in .gz, to be picked up and served by our internal static media
  // server as well as nginx when paired with the gzip_static module.
  if (IS_PRODUCTION) {
    config.plugins.push(new (require('compression-webpack-plugin'))({
      algorithm: 'gzip',
      regExp: /\.(js|map|css|svg|html|txt|ico|eot|ttf)$/,
    }));
  }

  return config;
}

module.exports = APPS.map(function(a) {
  return getConfig(a);
});

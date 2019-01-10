/*eslint-env node*/
module.exports = {
  presets: ['@babel/react', '@babel/env'],
  plugins: [
    'lodash',
    '@babel/plugin-proposal-object-rest-spread',
    ['babel-plugin-transform-builtin-extend', {globals: ['Array', 'Error']}],
  ],
};

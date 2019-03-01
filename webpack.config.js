const path = require('path');
const webpack = require('webpack');
const BundleTracker = require('webpack-bundle-tracker');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

module.exports = {
  context: __dirname,
  entry:  './assets/js/index.js',
  output: {
    path: path.resolve('./assets/bundles/'),
    filename: '[name]-[hash].js'
  },
  plugins: [
    new BundleTracker({
      path: __dirname,
      filename: 'webpack-stats.json'
    }),
    new CleanWebpackPlugin(
        ['assets/bundles/*']
    ),
    new MiniCssExtractPlugin('bundle.styles.css'),
    new webpack.ProvidePlugin({
      $: "jquery",
      jQuery: "jquery",
      'window.jQuery' : 'jquery'
    }),
  ],
  module: {
    rules:   [
      { test: /\.jsx?$/, exclude: /node_modules/, loader: 'babel-loader'},
      {test: /\.css$/, loader: 'style-loader!css-loader'},
      { test: /\.(svg|ttf|woff|woff2|eot)$/, loader: 'url-loader?limit=5000' },
    ]
  },
  resolve: {
    modules: ['node_modules', 'bower_components'],
    extensions: ['*', '.js', '.jsx']
  }
}
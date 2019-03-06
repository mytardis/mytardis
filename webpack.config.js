const path = require('path');
const webpack = require('webpack');
const BundleTracker = require('webpack-bundle-tracker');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const UglifyJsPlugin = require('uglifyjs-webpack-plugin');

module.exports = {
    context: __dirname,
    entry: './assets/js/index.js',
    output: {
        path: path.resolve('./assets/bundles/'),
        filename: '[name]-[hash].js'
    },
    optimization: {
        minimizer: [new UglifyJsPlugin()],
        splitChunks: {
            chunks: 'all',
            minSize: 30000,
            maxSize: 0,
            minChunks: 1,
            maxAsyncRequests: 5,
            maxInitialRequests: 3,
            automaticNameDelimiter: '~',
            name: true,
            cacheGroups: {
                vendors: {
                    test: /[\\/]node_modules[\\/]/,
                    priority: -10,
                },
                default: {
                    minChunks: 2,
                    priority: -20,
                    reuseExistingChunk: true
                }
            }
        }
    },
    plugins: [
        new BundleTracker({
            path: __dirname,
            filename: 'webpack-stats.json',
        }),
        new CleanWebpackPlugin(
            ['assets/bundles/*']
        ),
        new MiniCssExtractPlugin({
            filename: '[name]-[hash].styles.css',
        }),
        new webpack.ProvidePlugin({
            $: "jquery",
            jQuery: "jquery",
            'window.jQuery': 'jquery'
        }),
    ],
    module: {
        rules: [
            {test: /\.jsx?$/, exclude: /node_modules/, loader: 'babel-loader'},
            {
                test: /\.css$/,
                use: [
                    {
                        loader: MiniCssExtractPlugin.loader,
                        options: {
                            outputPath: 'static/bundles/',
                            publicPath: '../static/bundles/'
                        }
                    }, "css-loader"
                ]
            },
            {
                test: /\.(woff|woff2|)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
                loader: 'url-loader?limit=10000&mimetype=application/font-woff',
                options: {
                    name: '[name].[ext]',
                    outputPath: 'static/bundles/',
                    publicPath: '../static/bundles/'
                }
            },
            {   test: /\.(ttf|eot|svg)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
                loader: 'file-loader',
                options: {
                    name: '[name].[ext]',
                    publicPath: '/bundles/'
                }
            },
            {test: /backbone.js/, loader: 'imports-loader?define=>false'},
            {
                test: /\.(gif|png|jpe?g)$/i,
                loader: 'file-loader',
                options: {
                    name: '[name].[ext]',
                    publicPath: '/bundles/'
                }
            },
            {
                test: /\.less$/,
                use: [
                    {loader: "style-loader"},
                    {loader: "css-loader"},
                    {loader: "less-loader"}
                ]
            },

        ]
    },
    resolve: {
        modules: ['node_modules', 'bower_components'],
        extensions: ['*', '.js', '.jsx']
    }
}
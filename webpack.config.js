const path = require('path');
const webpack = require('webpack');
const BundleTracker = require('webpack-bundle-tracker');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

module.exports = {
    context: __dirname,
    entry: './assets/js/index.js',
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
            'window.jQuery': 'jquery'
        }),
    ],
    module: {
        rules: [
            {test: /\.jsx?$/, exclude: /node_modules/, loader: 'babel-loader'},
            {test: /\.css$/, loader: 'style-loader!css-loader',},
            {
                test: /\.(woff|woff2|)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
                loader: 'url-loader?limit=10000&mimetype=application/font-woff',
                options: {
                        name: '[name].[ext]',
                        outputPath: 'static/bundles/',
                        publicPath: '../static/bundles/'
                    }
            },
            {test: /\.(ttf|eot|svg)(\?v=[0-9]\.[0-9]\.[0-9])?$/, loader: 'file-loader'},
            {test: /backbone.js/, loader: 'imports-loader?define=>false'},
            {
                test: /\.(gif|png|jpe?g)$/i,
                use: [
                    'file-loader',
                    {
                        loader: 'image-webpack-loader',
                        options: {
                            disable: true,
                        },
                    },
                ],
            },
            {
                test: /\.less$/,
                use: [{
                    loader: "style-loader"
                }, {
                    loader: "css-loader"
                }, {
                    loader: "less-loader"
                }]
            },

        ]
    },
    resolve: {
        modules: ['node_modules', 'bower_components'],
        extensions: ['*', '.js', '.jsx']
    }
}
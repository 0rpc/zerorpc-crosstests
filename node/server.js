/* -*- coding: utf-8 -*-
 * Open Source Initiative OSI - The MIT License (MIT):Licensing
 *
 * The MIT License (MIT)
 * Copyright (c) 2016 François-Xavier Bourlet (bombela+zerorpc@gmail.com)
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy of
 * this software and associated documentation files (the "Software"), to deal in
 * the Software without restriction, including without limitation the rights to
 * use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
 * of the Software, and to permit persons to whom the Software is furnished to do
 * so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

var zerorpc = require("zerorpc");

var endpoint = process.argv[2];

var server = new zerorpc.Server({
	echo: function(v, reply) {
        console.log("echo %s <%s>", typeof(v), v);
		reply(null, v);
	},

	quit: function(reply) {
		console.log("exiting...");
		reply(null, null);
		server.close();
	},
});

server.bind(endpoint);

server.on("error", function(error) {
	console.error("RPC server error:", error);
});

console.log("Server started %s", endpoint);

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

const assert = require('assert');
var zerorpc = require("zerorpc");

var endpoint = process.argv[2];

var client = new zerorpc.Client();
client.connect(endpoint)

client.on("error", function(error) {
	console.error("RPC client error:", error);
	process.exit(-1);
});

var test_vals = [
	42,
	42.42,
	new Buffer('random bytes', 'ascii'),
	"unicode string",
];

var next_test = function() {
	if (test_vals.length == 0) {
		return quit_stage();
	}
	var v = test_vals.shift();
    console.log("sending %s <%s>", typeof(v), v);
	client.invoke("echo", v, function(error, r) {
		if(error) {
			console.error(error);
			process.exit(-1);
		} else {
			console.log("received %s <%s>", typeof(r), r);
			if (typeof(v) == 'object') {
				console.log("buffer equality");
				assert.ok(v.equals(r));
			} else {
				console.log("strict equality");
				assert.strictEqual(v, r);
			}
			next_test();
		}
	});
}
next_test();

function quit_stage() {
	client.invoke("quit", function(error, r) {
		if(error) {
			console.error(error);
			process.exit(-1);
		} else {
			console.log("All tests passed.");
			client.close();
		}
	});
}

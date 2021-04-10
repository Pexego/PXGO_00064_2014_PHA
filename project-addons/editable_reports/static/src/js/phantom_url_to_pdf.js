/*
 * Script de phantomjs para renderizar los informes.
 */
var system = require('system');

function replaceAll(text, busca, reemplaza) {
    while (text.toString().indexOf(busca) != -1)
        text = text.toString().replace(busca, reemplaza);
    return text;
};

RenderUrlsToFile = function(urls, session_id, dest_path) {
    var getFilename, next, page, retrieve, urlIndex, webpage;
    urlIndex = 0;
    webpage = require("webpage");
    page = null;
    getFilename = function() {
        return "rendermulti-" + urlIndex + ".pdf";
    };
    next = function(status, url, file) {
        page.close();
        return retrieve();
    };
    retrieve = function() {
        var url;
        if (urls.length > 0) {
            url = urls.shift();
            urlIndex++;
            var headerCallback = new Function('pageNum', 'numPages',
                'return \'<div style="border-bottom: 1px solid black; ' +
                'width: 100%; text-align: right; font-size: 12px;">' +
                'Página - \' + pageNum + \' de \' + numPages + ' +
                '\'</div>\';');
            var parser = document.createElement('a');
            parser.href = url;
            phantom.addCookie({
              'name': 'session_id',
              'value': session_id,
              'domain': parser.hostname
            });
            page = webpage.create();
            page.paperSize = {
                format: 'A4',
                orientation: 'portrait',
                margin: '0.5cm',
                header: {
                    height: '1.5cm',
                    contents: phantom.callback(headerCallback)
                },
            };
            page.settings.userAgent = "Phantom.js bot";
            return page.open(url, function(status) {
                var file;
                file = getFilename();
                if (status === 'success') {
                    return window.setTimeout((function() {
                        dest_file = replaceAll(replaceAll(url, ':', ''), '/', '');
                        dest_file = dest_path + '/' + dest_file + '.pdf';
                        page.render(dest_file, {format: 'pdf', quality: '100'});
                        return next(status, url, file);
                    }), 5000);
                } else {
                    return next(status, url, file);
                }
            });
        } else {
            return phantom.exit();
        }
    };
    return retrieve();
};

var urls = null;
var session_id = null;
var dest_path = null;
if (system.args.length > 3) {
    session_id = system.args[1];
    dest_path = system.args[2];
    urls = Array.prototype.slice.call(system.args, 3);
} else {
    console.log('Usage: phantomjs phantom_url_to_pdf.js session_id destination_path [url1, url2, ...]');
    phantom.exit();
}

RenderUrlsToFile(urls, session_id, dest_path);

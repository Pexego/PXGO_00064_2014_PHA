/*
 * Script de phantomjs para renderizar los documentos de calidad.
 */
var system = require("system");

function replaceAll(text, busca, reemplaza) {
    while (text.toString().indexOf(busca) != -1)
        text = text.toString().replace(busca,reemplaza);
    return text;
};

function extractWeight(text) {
    posWeight = text.indexOf('?weight=');
    if (posWeight != -1) {
        return text.substring(posWeight + 8, posWeight + 10);
    } else {
        return '';
    }
};

function extractData(text) {
    txt = text.replace(/~/g, ' ');
    posProd     = txt.indexOf('#prod=');
    posProtName = txt.indexOf('#protname=');
    posProt     = txt.indexOf('#prot=');
    posProduct  = txt.indexOf('#product=');
    posLot      = txt.indexOf('#lot=');
    posDate     = txt.indexOf('#date=');
    return {
        production: ((posProd > -1 && posProtName > -1) ? txt.substring(posProd + 6, posProtName) : '¿?'),
        protocolName: ((posProtName > -1 && posProt > -1) ? txt.substring(posProtName + 10, posProt) : '¿?'),
        protocol: ((posProt > -1 && posProduct > -1) ? txt.substring(posProt + 6, posProduct) : '¿?'),
        product: ((posProduct > -1 && posLot > -1) ? txt.substring(posProduct + 9, posLot) : '¿?'),
        lot: ((posLot > -1 && posDate > -1) ? txt.substring(posLot + 5, posDate) : '¿?'),
        date: ((posDate > -1) ? txt.substring(posDate + 6) : '¿?')
    };
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
            var data = extractData(url);
            var headerCallback = new Function('pageNum', 'numPages',
                'return \'<div style="border-bottom: 1px solid black; ' +
                'width: 100%; text-align: right; font-size: 12px;">' +
                data.production + ' - ' + data.protocolName + ' - ' +
                data.protocol + ' - \' + pageNum + \' de \' + numPages + ' +
                '\'<br>' +
                data.product + ' - ' + data.lot + ' - ' + data.date +
                '</div>\';');
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
                if (status === "success") {
                    return window.setTimeout((function() {
                        dest_file = replaceAll(replaceAll(url, ':', ''), '/', '');
                        weight = extractWeight(dest_file);
                        if (weight > '') {
                            dest_file = dest_file.substring(0, dest_file.indexOf('?weight='));
                            dest_file = weight + '-' + dest_file;
                        };
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
    console.log("Usage: phantomjs render_multi_url.js [domain.name1, domain.name2, ...]");
    phantom.exit();
}

RenderUrlsToFile(urls, session_id, dest_path);

$(function() {
    // Parameters object
    openerp.sortedMenus = {};

    // Flag to avoid multiple timeout chaining
    openerp.sortedMenus.timeout = 0;

    // Target class to order items
    openerp.sortedMenus.target = '.graph_widget .dropdown-menu:not(.sorted)';

    // Options for the observer (which mutations to observe)
    var config = {attributes: false, subtree: true, childList: true};

    // Callback function to execute when mutations are observed
    var callback = function(mutationsList) {
        // Ignore mutationList and search directly for target
        if (document.documentURI && document.documentURI.includes('view_type=graph&')) {
            if ($(openerp.sortedMenus.target).length > 0 &&
                  openerp.sortedMenus.timeout == 0) {
                openerp.sortedMenus.timeout = setTimeout(function() {
                    $(openerp.sortedMenus.target).each(function(idx) {
                        options = $(this).children('li').detach();
                        options.sort(function(a, b) {
                            var vA = $('a', a).text();
                            var vB = $('a', b).text();
                            return (vA < vB) ? -1 : (vA > vB) ? 1 : 0;
                        });
                        $(this).append(options);
                        $(this).addClass('sorted');
                    });
                    openerp.sortedMenus.timeout = 0;
                }, 500);
            }
        }
    };

    // Create an observer instance linked to the callback function
    openerp.sortedMenus.observer = new MutationObserver(callback);

    // Start observing the target node for configured mutations
    openerp.sortedMenus.observer.observe(document, config);
});

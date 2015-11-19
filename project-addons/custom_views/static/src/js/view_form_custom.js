(function() {
    var instance = openerp;

    instance.web.form.WidgetButton = instance.web.form.WidgetButton.extend({
        template: 'WidgetButton',
        init: function(field_manager, node) {
            this._super(field_manager, node);
        },
        start: function() {
            this._super();
        },
        on_click: function() {
            this._super();
        },
        execute_action: function() {
            var self = this;
            var exec_action = function() {
                if (self.node.attrs.confirm) {
                    var def = $.Deferred();
                    var dialog = new instance.web.Dialog(this, {
                        title: _t('Confirm'),
                        buttons: [
                            {text: _t("Cancel"), click: function() {
                                    this.parents('.modal').modal('hide');
                                }
                            },
                            {text: _t("Ok"), click: function() {
                                    var self2 = this;
                                    self.on_confirmed().always(function() {
                                        self2.parents('.modal').modal('hide');
                                    });
                                }
                            }
                        ],
                    }, $('<div/>').text(self.node.attrs.confirm)).open();
                    dialog.on("closing", null, function() {def.resolve();});
                    return def.promise();
                } else {
                    return self.on_confirmed();
                }
            };
            if (!this.node.attrs.special && (this.view.get('actual_mode') != 'view')) {
                return this.view.recursive_save().then(exec_action);
            } else {
                return exec_action();
            }
        },
        on_confirmed: function() {
            return this._super();
        },
        check_disable: function() {
            this._super();
        }
    });
})();
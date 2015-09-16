openerp.sale_stock_data = function(openerp) {
  openerp.web.form.FieldUrl.include({
    render_value: function() {
        this._super();
        var tmp = this.get('value');
        var s = /(\w+):(.+)|^\.{0,2}\//.exec(tmp);
        if (!s) {
            tmp = "http://" + this.get('value');
        }
        if(this.node.attrs.url_value){
            _t = openerp.web._t
            this.$el.find('a').attr('href', tmp).text(_t(this.node.attrs.url_value));
        }
    }
  });
}


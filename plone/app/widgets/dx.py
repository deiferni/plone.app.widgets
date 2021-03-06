# -*- coding: utf-8 -*-

from Products.CMFCore.utils import getToolByName
from datetime import date
from datetime import datetime
from plone.app.widgets import base
from plone.app.widgets.utils import NotImplemented
from plone.app.widgets.utils import get_date_options
from plone.app.widgets.utils import get_portal_url
from plone.app.widgets.utils import get_time_options
from z3c.form import interfaces as z3cform_interfaces
from z3c.form.browser.select import SelectWidget as z3cform_SelectWidget
from z3c.form.converter import BaseDataConverter
from z3c.form.widget import Widget
from zope.component import adapts
from zope.component import queryUtility
from zope.interface import implementsOnly
from zope.schema.interfaces import ICollection
from zope.schema.interfaces import IDate
from zope.schema.interfaces import IDatetime
from zope.schema.interfaces import IList
from zope.schema.interfaces import IVocabularyFactory

import json


class IDateWidget(z3cform_interfaces.ITextWidget):
    """Marker interface for the DateWidget."""


class IDatetimeWidget(z3cform_interfaces.ITextWidget):
    """Marker interface for the DatetimeWidget."""


class ISelectWidget(z3cform_interfaces.ISelectWidget):
    """Marker interface for the SelectWidget."""


class IAjaxSelectWidget(z3cform_interfaces.ITextWidget):
    """Marker interface for the Select2Widget."""


class IQueryStringWidget(z3cform_interfaces.ITextWidget):
    """Marker interface for the QueryStringWidget."""


class IRelatedItemsWidget(z3cform_interfaces.ITextWidget):
    """Marker interface for the RelatedItemsWidget."""


class DateWidgetConverter(BaseDataConverter):
    """Data converter for date fields."""

    adapts(IDate, IDateWidget)

    def toWidgetValue(self, value):
        """Converts from field value to widget.

        :param value: Field value.
        :type value: date

        :returns: Date in format `Y-m-d`
        :rtype: string
        """
        if value is self.field.missing_value:
            return u''
        return ('{value.year:}-{value.month:02}-{value.day:02}'
                ).format(value=value)

    def toFieldValue(self, value):
        """Converts from widget value to field.

        :param value: Value inserted by date widget.
        :type value: string

        :returns: `date.date` object.
        :rtype: date
        """
        if not value:
            return self.field.missing_value
        return date(*map(int, value.split('-')))


class DatetimeWidgetConverter(BaseDataConverter):
    """Data converter for datetime fields."""

    adapts(IDatetime, IDatetimeWidget)

    def toWidgetValue(self, value):
        """Converts from field value to widget.

        :param value: Field value.
        :type value: datetime

        :returns: Datetime in format `Y-m-d H:M`
        :rtype: string
        """
        if value is self.field.missing_value:
            return u''
        return ('{value.year:}-{value.month:02}-{value.day:02} '
                '{value.hour:02}:{value.minute:02}').format(value=value)

    def toFieldValue(self, value):
        """Converts from widget value to field.

        :param value: Value inserted by datetime widget.
        :type value: string

        :returns: `datetime.datetime` object.
        :rtype: datetime
        """
        if not value:
            return self.field.missing_value
        tmp = value.split(' ')
        if not tmp[0]:
            return self.field.missing_value
        value = tmp[0].split('-')
        value += tmp[1].split(':')
        return datetime(*map(int, value))


class AjaxSelectWidgetConverter(BaseDataConverter):
    """Data converter for ICollection."""

    adapts(ICollection, IAjaxSelectWidget)

    def toWidgetValue(self, value):
        """Converts from field value to widget.

        :param value: Field value.
        :type value: list |tuple | set

        :returns: Items separated using separator defined on widget
        :rtype: string
        """
        if not value:
            return self.field.missing_value
        separator = getattr(self.widget, 'separator', ';')
        return separator.join(unicode(v) for v in value)

    def toFieldValue(self, value):
        """Converts from widget value to field.

        :param value: Value inserted by AjaxSelect widget.
        :type value: string

        :returns: List of items
        :rtype: list | tuple | set
        """
        collectionType = self.field._type
        if isinstance(collectionType, tuple):
            collectionType = collectionType[-1]
        if not len(value):
            return self.field.missing_value
        valueType = self.field.value_type._type
        if isinstance(valueType, tuple):
            valueType = valueType[0]
        separator = getattr(self.widget, 'separator', ';')
        return collectionType(valueType and valueType(v) or v
                              for v in value.split(separator))


class RelatedItemsDataConverter(BaseDataConverter):
    """Data converter for ICollection."""

    adapts(ICollection, IRelatedItemsWidget)

    def toWidgetValue(self, value):
        """Converts from field value to widget.

        :param value: List of catalog brains.
        :type value: list

        :returns: List of of UID separated by separator defined on widget.
        :rtype: string
        """
        if not value:
            return self.field.missing_value
        separator = getattr(self.widget, 'separator', ';')
        return separator.join(unicode(v.UID()) for v in value)

    def toFieldValue(self, value):
        """Converts from widget value to field.

        :param value: List of UID's separated by separator defined
        :type value: string

        :returns: List of content objects
        :rtype: list | tuple | set
        """
        collectionType = self.field._type
        if isinstance(collectionType, tuple):
            collectionType = collectionType[-1]
        if not len(value):
            return self.field.missing_value

        catalog = getToolByName(self.widget.context, 'portal_catalog')
        separator = getattr(self.widget, 'separator', ';')
        value = value.split(separator)
        value = [v.split('/')[0] for v in value]
        results = catalog(UID=value)
        return collectionType(item.getObject() for item in results)


class QueryStringDataConverter(BaseDataConverter):
    """Data converter for IList."""

    adapts(IList, IQueryStringWidget)

    def toWidgetValue(self, value):
        """Converts from field value to widget.

        :param value: Query string.
        :type value: list

        :returns: Query string converted to JSON.
        :rtype: string
        """
        if value is self.field.missing_value:
            return self.field.missing_value
        return json.dumps(value)

    def toFieldValue(self, value):
        """Converts from widget value to field.

        :param value: Query string.
        :type value: string

        :returns: Query string.
        :rtype: list
        """
        if value is self.field.missing_value:
            return self.field.missing_value
        return json.loads(value)


class BaseWidget(Widget):
    """Base widget for z3c.form."""

    pattern = None
    pattern_options = {}

    def _base(self, pattern, pattern_options={}):
        """Base widget class."""
        raise NotImplemented

    def _base_args(self):
        """Method which will calculate _base class arguments.

        Returns (as python dictionary):
            - `pattern`: pattern name
            - `pattern_options`: pattern options

        :returns: Arguments which will be passed to _base
        :rtype: dict
        """
        if self.pattern is None:
            raise NotImplemented("'pattern' options not provided.")
        return {
            'pattern': self.pattern,
            'pattern_options': self.pattern_options,
        }

    def render(self):
        """Render widget.

        :returns: Widget's HTML.
        :rtype: string
        """
        if self.mode != 'input':
            return super(BaseWidget, self).render()
        return self._base(**self._base_args()).render()


class DateWidget(BaseWidget):
    """Date widget for z3c.form."""

    _base = base.InputWidget
    _converter = DateWidgetConverter
    _formater = 'date'

    implementsOnly(IDateWidget)

    pattern = 'pickadate'
    pattern_options = BaseWidget.pattern_options.copy()

    def _base_args(self):
        """Method which will calculate _base class arguments.

        Returns (as python dictionary):
            - `pattern`: pattern name
            - `pattern_options`: pattern options
            - `name`: field name
            - `value`: field value

        :returns: Arguments which will be passed to _base
        :rtype: dict
        """
        args = super(DateWidget, self)._base_args()
        args['name'] = self.name
        args['value'] = (self.request.get(self.name,
                                          self.value) or u'').strip()

        args.setdefault('pattern_options', {})

        args['pattern_options'].setdefault('date', {})
        args['pattern_options']['date'] = base.dict_merge(
            args['pattern_options']['date'],
            get_date_options(self.request))

        args['pattern_options']['time'] = False

        return args

    def render(self):
        """Render widget.

        :returns: Widget's HTML.
        :rtype: string
        """
        if self.mode != 'display':
            return super(DateWidget, self).render()

        if not self.value:
            return ''

        field_value = self._base_converter(
            self.field, self).toFieldValue(self.value)
        if field_value is self.fields.missing_value:
            return u''

        formatter = self.request.locale.dates.getFormatter(
            self._formater, "short")
        if field_value.year > 1900:
            return formatter.format(field_value)

        # due to fantastic datetime.strftime we need this hack
        # for now ctime is default
        return field_value.ctime()


class DatetimeWidget(DateWidget):
    """Datetime widget for z3c.form."""

    _converter = DatetimeWidgetConverter
    _formater = 'dateTime'

    implementsOnly(IDatetimeWidget)

    pattern_options = DateWidget.pattern_options.copy()

    def _base_args(self):
        """Method which will calculate _base class arguments.

        Returns (as python dictionary):
            - `pattern`: pattern name
            - `pattern_options`: pattern options
            - `name`: field name
            - `value`: field value

        :returns: Arguments which will be passed to _base
        :rtype: dict
        """
        args = super(DatetimeWidget, self)._base_args()

        if args['value'] and len(args['value'].split(' ')) == 1:
            args['value'] += ' 00:00'

        if args['pattern_options']['time'] is False:
            args['pattern_options']['time'] = {}

        args['pattern_options']['time'] = base.dict_merge(
            args['pattern_options']['time'],
            get_time_options(self.request))

        return args


class SelectWidget(BaseWidget, z3cform_SelectWidget):
    """Select widget for z3c.form."""

    _base = base.SelectWidget

    implementsOnly(ISelectWidget)

    pattern = 'select2'
    pattern_options = BaseWidget.pattern_options.copy()
    multiple = False

    def _base_args(self):
        """Method which will calculate _base class arguments.

        Returns (as python dictionary):
            - `pattern`: pattern name
            - `pattern_options`: pattern options
            - `name`: field name
            - `value`: field value
            - `multiple`: field multiple
            - `items`: field items from which we can select to

        :returns: Arguments which will be passed to _base
        :rtype: dict
        """
        args = super(SelectWidget, self)._base_args()
        args['name'] = self.name
        args['value'] = self.value
        args['multiple'] = self.multiple

        items = []
        for item in self.items():
            items.append((item['value'], item['content']))
        args['items'] = items

        return args


class AjaxSelectWidget(BaseWidget):
    """Ajax select widget for z3c.form."""

    _base = base.InputWidget

    implementsOnly(IAjaxSelectWidget)

    pattern = 'select2'
    pattern_options = BaseWidget.pattern_options.copy()

    separator = ';'
    vocabulary = None

    def _base_args(self):
        """Method which will calculate _base class arguments.

        Returns (as python dictionary):
            - `pattern`: pattern name
            - `pattern_options`: pattern options
            - `name`: field name
            - `value`: field value

        :returns: Arguments which will be passed to _base
        :rtype: dict
        """

        args = super(AjaxSelectWidget, self)._base_args()
        args['name'] = self.name
        args['value'] = self.value
        args['pattern_options']['separator'] = self.separator

        vocabulary_factory = getattr(self.field, 'vocabulary_factory', None)
        if not self.vocabulary:
            self.vocabulary = vocabulary_factory

        # get url which will be used to lookup vocabulary
        if self.vocabulary:
            vocabulary_url = '%s/@@getVocabulary?name=%s' % (
                get_portal_url(self.context), self.vocabulary)
            args['pattern_options']['vocabularyUrl'] = vocabulary_url

            # initial values
            if self.value:
                vocabulary = queryUtility(IVocabularyFactory, self.vocabulary)
                if vocabulary:
                    initialValues = {}
                    vocabulary = vocabulary(self.context)
                    if self.vocabulary == 'plone.app.vocabularies.Catalog':
                        uids = self.value.split(self.separator)
                        catalog = getToolByName(self.context, 'portal_catalog')
                        for item in catalog(UID=uids):
                            initialValues[item.UID] = item.Title
                    else:
                        for value in self.value.split(self.separator):
                            try:
                                term = vocabulary.getTerm(value)
                                initialValues[term.token] = term.title
                            except LookupError:
                                initialValues[value] = value
                args['pattern_options']['initialValues'] = initialValues

        return args


class QueryStringWidget(BaseWidget):
    """QueryString widget for z3c.form."""

    _base = base.InputWidget

    implementsOnly(IQueryStringWidget)

    pattern = 'querystring'
    pattern_options = BaseWidget.pattern_options.copy()

    def _base_args(self):
        """Method which will calculate _base class arguments.

        Returns (as python dictionary):
            - `pattern`: pattern name
            - `pattern_options`: pattern options
            - `name`: field name
            - `value`: field value

        :returns: Arguments which will be passed to _base
        :rtype: dict
        """
        args = super(QueryStringWidget, self)._base_args()
        args['name'] = self.name
        args['value'] = self.value
        args['pattern_options']['indexOptionsUrl'] = '%s/@@qsOptions' % (
            get_portal_url(self.context))
        return args


class RelatedItemsWidget(AjaxSelectWidget):
    """RelatedItems widget for z3c.form."""

    pattern = 'relateditems'
    pattern_options = AjaxSelectWidget.pattern_options.copy()

    implementsOnly(IRelatedItemsWidget)

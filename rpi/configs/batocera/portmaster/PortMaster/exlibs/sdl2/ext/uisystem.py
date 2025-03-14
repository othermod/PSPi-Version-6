"""User interface elements."""
from .compat import isiterable, stringify
from .ebs import System, World
from .events import EventHandler
from .sprite import Sprite
from .. import events, mouse, keyboard, rect

__all__ = [
    "RELEASED", "HOVERED", "PRESSED", "BUTTON", "CHECKBUTTON", "TEXTENTRY",
    "UIProcessor", "UIFactory"
]


RELEASED = 0x0000
HOVERED = 0x0001
PRESSED = 0x0002

BUTTON = 0x0001
CHECKABLE = 0x0002
CHECKBUTTON = (CHECKABLE | BUTTON)
TEXTENTRY = 0x0004



def _compose_button(obj):
    """Binds button attributes to the object, so it can be properly
    processed by the UIProcessor.

    Note: this is an internal helper method to avoid multiple
    inheritance and composition issues and should not be used by user
    code.
    """
    obj.uitype = BUTTON
    obj.state = RELEASED
    obj.motion = EventHandler(obj)
    obj.pressed = EventHandler(obj)
    obj.released = EventHandler(obj)
    obj.click = EventHandler(obj)
    obj.events = {
        events.SDL_MOUSEMOTION: obj.motion,
        events.SDL_MOUSEBUTTONDOWN: obj.pressed,
        events.SDL_MOUSEBUTTONUP: obj.released
        }


def _compose_checkbutton(obj):
    """Binds check button attributes to the object, so it can be properly
    processed by the UIProcessor.

    Note: this is an internal helper method to avoid multiple
    inheritance and composition issues and should not be used by user
    code.
    """
    _compose_button(obj)
    obj.uitype = CHECKBUTTON
    obj.checked = False


def _compose_textentry(obj):
    """Binds text entry attributes to the object, so it can be properly
    processed by the UIProcessor.

    Note: this is an internal helper method to avoid multiple
    inheritance and composition issues and should not be used by user
    code.
    """
    obj.uitype = TEXTENTRY
    obj.text = ""
    obj.motion = EventHandler(obj)
    obj.pressed = EventHandler(obj)
    obj.released = EventHandler(obj)
    obj.keydown = EventHandler(obj)
    obj.keyup = EventHandler(obj)
    obj.input = EventHandler(obj)
    obj.editing = EventHandler(obj)
    obj.events = {
        events.SDL_MOUSEMOTION: obj.motion,
        events.SDL_MOUSEBUTTONDOWN: obj.pressed,
        events.SDL_MOUSEBUTTONUP: obj.released,
        events.SDL_TEXTEDITING: obj.editing,
        events.SDL_TEXTINPUT: obj.input,
        events.SDL_KEYDOWN: obj.keydown,
        events.SDL_KEYUP: obj.keyup
        }


class UIFactory(object):
    """A simple UI factory for creating GUI elements for software- or
    texture-based rendering."""
    def __init__(self, spritefactory, **kwargs):
        """Creates a new UIFactory.

        The additional kwargs will be stored internally and passed to the
        UI creation methods as arguments. Hence they can act as default
        arguments to be passed to each and every UI element to be
        created.
        """
        self.spritefactory = spritefactory
        self.default_args = kwargs

    def from_image(self, uitype, fname):
        """Creates a new UI element from the passed image file."""
        sprite = self.spritefactory.from_image(fname)
        if uitype == BUTTON:
            _compose_button(sprite)
        elif uitype == CHECKBUTTON:
            _compose_checkbutton(sprite)
        elif uitype == TEXTENTRY:
            _compose_textentry(sprite)
        else:
            del sprite
            raise ValueError("uitype must be a valid UI type identifier")
        return sprite

    def from_surface(self, uitype, surface, free=False):
        """Creates a new UI element from the passed SDL surface."""
        sprite = self.spritefactory.from_surface(surface, free)
        if uitype == BUTTON:
            _compose_button(sprite)
        elif uitype == CHECKBUTTON:
            _compose_checkbutton(sprite)
        elif uitype == TEXTENTRY:
            _compose_textentry(sprite)
        else:
            del sprite
            raise ValueError("uitype must be a valid UI type identifier")
        return sprite

    def from_object(self, uitype, obj):
        """Creates a new UI element from an arbitrary object."""
        sprite = self.spritefactory.from_object(obj)
        if uitype == BUTTON:
            _compose_button(sprite)
        elif uitype == CHECKBUTTON:
            _compose_checkbutton(sprite)
        elif uitype == TEXTENTRY:
            _compose_textentry(sprite)
        else:
            del sprite
            raise ValueError("uitype must be a valid UI type identifier")
        return sprite

    def from_color(self, uitype, color, size):
        """Creates a new UI element using a certain color."""
        sprite = self.spritefactory.from_color(color, size)
        if uitype == BUTTON:
            _compose_button(sprite)
        elif uitype == CHECKBUTTON:
            _compose_checkbutton(sprite)
        elif uitype == TEXTENTRY:
            _compose_textentry(sprite)
        else:
            del sprite
            raise ValueError("uitype must be a valid UI type identifier")
        return sprite

    def create_button(self, **kwargs):
        """Creates a new Sprite that can react on mouse events."""
        args = self.default_args.copy()
        args.update(kwargs)
        sprite = self.spritefactory.create_sprite(**args)
        _compose_button(sprite)
        return sprite

    def create_checkbutton(self, **kwargs):
        """Creates a new Sprite that can react on mouse events and
        retains its state."""
        args = self.default_args.copy()
        args.update(kwargs)
        sprite = self.spritefactory.create_sprite(**args)
        _compose_checkbutton(sprite)
        return sprite

    def create_text_entry(self, **kwargs):
        """Creates a new Sprite that can react on text input."""
        args = self.default_args.copy()
        args.update(kwargs)
        sprite = self.spritefactory.create_sprite(**args)
        _compose_textentry(sprite)
        return sprite

    def __repr__(self):
        return "UIFactory(spritefactory=%s, default_args=%s)" % \
            (self.spritefactory, self.default_args)


class UIProcessor(System):
    """A processing system for user interface elements and events."""
    def __init__(self):
        """Creates a new UIProcessor."""
        super(UIProcessor, self).__init__()
        self.componenttypes = (Sprite,)
        self._nextactive = None
        self._activecomponent = None
        self.handlers = {
            events.SDL_MOUSEMOTION: self.mousemotion,
            events.SDL_MOUSEBUTTONDOWN: self.mousedown,
            events.SDL_MOUSEBUTTONUP: self.mouseup,
            events.SDL_TEXTINPUT: self.textinput
            }

    def activate(self, component):
        """Activates a control to receive input."""
        if self._activecomponent and self._activecomponent != component:
            self.deactivate(self._activecomponent)

        if (component.uitype & TEXTENTRY):
            area = rect.SDL_Rect(component.x, component.y,
                                 component.size[0], component.size[1])
            keyboard.SDL_SetTextInputRect(area)
            keyboard.SDL_StartTextInput()
        self._activecomponent = component

    def deactivate(self, component):
        """Deactivates the currently active control."""
        if component == self._activecomponent:
            if (self._activecomponent.uitype & TEXTENTRY):
                keyboard.SDL_StopTextInput()
            self._activecomponent = None

    def passevent(self, component, event):
        """Passes the event to a component without any additional checks
        or restrictions.
        """
        component.events[event.type](event)

    def textinput(self, component, event):
        """Checks, if an active component is available and matches the
        passed component and passes the event on to that component."""
        if self._activecomponent == component:
            if (component.uitype & TEXTENTRY):
                component.text += stringify(event.text.text, "utf-8")
            component.events[event.type](event)

    def mousemotion(self, component, event):
        """Checks, if the event's motion position is on the component
        and executes the component's event handlers on demand.

        If the motion event position is not within the area of the
        component, nothing will be done. In case the component is a
        Button, its state will be adjusted to reflect, if it is
        currently hovered or not.
        """
        x1, y1, x2, y2 = component.area
        if event.motion.x >= x1 and event.motion.x < x2 and \
                event.motion.y >= y1 and event.motion.y < y2:
            # Within the area of the component, raise the event on it.
            component.events[event.type](event)
            if (component.uitype & BUTTON):
                component.state |= HOVERED
        elif (component.uitype & BUTTON):
            # The mouse is not within the area of the button, reset the
            # state
            component.state &= ~HOVERED

    def mousedown(self, component, event):
        """Checks, if the event's button press position is on the
        component and executes the component's event handlers on demand.

        If the button press position is not within the area of the
        component, nothing will be done. In case the component is a
        Button, its state will be adjusted to reflect, if it is
        currently pressed or not. In case the component is a TextEntry and
        the pressed button is the primary mouse button, the component will
        be marked as the next control to activate for text input.
        """
        x1, y1, x2, y2 = component.area
        if event.button.x >= x1 and event.button.x < x2 and \
                event.button.y >= y1 and event.button.y < y2:
            # Within the area of the component, raise the event on it.
            component.events[event.type](event)
            if (component.uitype & BUTTON):
                component.state = PRESSED | HOVERED
                if (component.uitype & CHECKABLE):
                    if event.button.button == mouse.SDL_BUTTON_LEFT:
                        component.checked = not component.checked
            # Since we loop over all components, and might deactivate
            # some, store it temporarily for later activation.
            self._nextactive = component
        elif (component.uitype & BUTTON):
            component.state &= ~PRESSED

    def mouseup(self, component, event):
        """Checks, if the event's button release position is on the
        component and executes the component's event handlers on demand.

        If the button release position is not within the area of the
        component, nothing will be done. In case the component is a
        Button, its state will be adjusted to reflect, whether it is
        hovered or not. If the button release followed a button press on
        the same component and if the button is the primary button, the
        click() event handler is invoked, if the component is a Button.
        """
        x1, y1, x2, y2 = component.area
        if event.button.x >= x1 and event.button.x < x2 and \
                event.button.y >= y1 and event.button.y < y2:
            # Within the area of the component, raise the event on it.
            component.events[event.type](event)
            if (component.uitype & BUTTON):
                if (component.state & PRESSED) == PRESSED:
                    # Was pressed already, now it is a click
                    component.click(event)
                component.state = RELEASED | HOVERED
        elif (component.uitype & BUTTON):
            component.state &= ~HOVERED

    def dispatch(self, obj, event):
        """Passes an event to the given object.

        If obj is a World object, UI relevant components will receive
        the event, if they support the event type.

        If obj is a single object, obj.events MUST be a dictionary
        consisting of SDL event type identifiers and EventHandler
        instances bound to the object. obj also must have a 'uitype' attribute
        referring to the UI type of the object.
        If obj is an iterable, such as a list or set, every item within
        obj MUST feature an 'events' and 'uitype' attribute as described
        above.
        """
        if event is None:
            return

        handler = self.handlers.get(event.type, self.passevent)
        if isinstance(obj, World):
            for ctype in self.componenttypes:
                items = obj.get_components(ctype)
                items = [(v, e) for v in items for e in (event,)
                         if hasattr(v, "events") and hasattr(v, "uitype") \
                            and e.type in v.events]
                if len(items) > 0:
                    arg1, arg2 = zip(*items)
                    map(handler, arg1, arg2)
        elif isiterable(obj):
            items = [(v, e) for v in obj for e in (event,)
                     if e.type in v.events]
            if len(items) > 0:
                for v, e in items:
                    handler(v, e)
        elif event.type in obj.events:
            handler(obj, event)
        if self._nextactive is not None:
            self.activate(self._nextactive)
            self._nextactive = None

    def process(self, world, components):
        """The UIProcessor class does not implement the process() method
        by default. Instead it uses dispatch() to send events around to
        components.
        """
        pass

    def __repr__(self):
        return "UIProcessor()"

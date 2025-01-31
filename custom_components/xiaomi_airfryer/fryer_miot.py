"""
Support for Xiaomi AirFryer.

"""
import enum
from typing import Any, Dict, Tuple
import logging
import click

from miio.click_common import command, format_output
from miio.device import DeviceStatus
from miio.miot_device import MiotDevice

_LOGGER = logging.getLogger(__name__)


# http://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:air-fryer:0000A0A4:careli-maf01:1
MIOT_MAPPING = {
    "status": {"siid": 2, "piid": 1},  # read, notify
    "device_fault": {"siid": 2, "piid": 2},  # read, notify
    "target_time": {"siid": 2, "piid": 3},  # read, notify, write
    "target_temperature": {"siid": 2, "piid": 4},  # read, notify, write
    "left_time": {"siid": 2, "piid": 5},  # read, notify
    "recipe_id": {"siid": 3, "piid": 1},  # read, notify, write
    "recipe_name": {"siid": 3, "piid": 2},  # read, notify, write
    "appoint_time": {"siid": 3, "piid": 5},  # read, notify, write
    "food_quanty": {"siid": 3, "piid": 6},  # read, notify, write
    "preheat_switch": {"siid": 3, "piid": 7},  # read, notify, write
    "appoint_time_left": {"siid": 3, "piid": 8},  # read, notify, write
    "recipe_sync": {"siid": 3, "piid": 9},  # read, notify, write
    "turn_pot": {"siid": 3, "piid": 10},  # read, notify, write
    "start_cook": {"siid": 2, "aiid": 1},
    "cancel_cooking": {"siid": 2, "aiid": 2},
    "pause": {"siid": 2, "aiid": 3},
    "start_custom_cook": {"siid": 3, "aiid": 1},
    "resume_cooking": {"siid": 3, "aiid": 2},
}


class DeviceException(Exception):
    """Exception wrapping any communication errors with the device."""


class Status(enum.Enum):
    """Status"""

    Unknown = -1
    Shutdown = 0
    Standby = 1
    Pause = 2
    Appointment = 3
    Cooking = 4
    Preheat = 5
    Cooked = 6
    PreheatFinish = 7
    PreheatPause = 8
    Pause2 = 9
    Keepwarm = 10
    KeepwarmPause = 11
    KeepwarmFinish = 12
    CrispyRoast = 13
    Degrease = 14


class DeviceFault(enum.Enum):
    """Device Fault"""

    Unknown = -1
    NoFaults = 0
    E1 = 1
    E2 = 2
    E3 = 3


class FoodQuanty(enum.Enum):
    """Food Quanty"""

    Unknown = -1
    Null = 0
    Single = 1
    Double = 2
    Half = 3
    Full = 4


class TurnPot(enum.Enum):
    """Turn Pot"""

    Unknown = -1
    NotTurnPot = 0
    SwitchOff = 1
    TurnPot = 2


class PreheatSwitch(enum.Enum):
    """Turn Pot"""

    Unknown = -1
    Null = 0
    Off = 1
    On = 2


class RecipeId(enum.Enum):
    Manual = "M0"
    FrenchFries = "M1"
    ChickenWing = "M2"
    SweetPotato = "M3"
    Cake = "M4"
    Defrost = "M5"
    DriedFruit = "M6"
    Yogurt = "M7"


class RecipeToCommand(enum.Enum):
    """
    It is possible to use custom recipes here, may be later
    Recipes should be in this format, but check specs of your device, the length of params can be different
    careli.fryer.maf02 = [ recipeId, name, targetTime, targetTemperature, appointTime, foodQuantity, preheat ]
    """

    Manual = ["M0", "", 0, 0, 0, 0, 0]
    FrenchFries = ["M1", "", 15, 200, 0, 3, 0]
    ChickenWing = ["M2", "", 15, 180, 0, 1, 0]
    SweetPotato = ["M3", "", 30, 200, 0, 1, 0]
    Cake = ["M4", "", 30, 160, 0, 0, 0]
    Defrost = ["M5", "", 15, 40, 0, 0, 0]
    DriedFruit = ["M6", "", 240, 40, 0, 0, 0]
    Yogurt = ["M7", "", 480, 40, 0, 0, 0]


class RecipeName(enum.Enum):
    Manual = "Ручной"
    FrenchFries = "Картофель Фри"
    ChickenWing = "Куриные Крылья"
    SweetPotato = "Сладкий картофель"
    Defrost = "Разморозка"
    DriedFruit = "Сухофрукты"
    Yogurt = "Йогурт"
    Cake = "Торт"


class FryerStatusMiot(DeviceStatus):
    """Container for status reports for Xiaomi FryerStatusMiot."""

    def __init__(self, data: Dict[str, Any]) -> None:
        self.data = data

    @property
    def is_on(self) -> bool:
        """True if device is currently on."""
        return self.data["status"] not in [0, 1, 6, 9]

    @property
    def mode(self) -> int:
        """Mode."""
        return self.data.get("mode")

    @property
    def status(self) -> int:
        """Operation status."""
        try:
            return Status(self.data["status"]).value
        except ValueError:
            _LOGGER.error("Unknown Status (%s)", self.data["status"])
            return Status.Unknown.value

    @property
    def device_fault(self) -> int:
        """Device Fault."""
        try:
            return DeviceFault(self.data["device_fault"]).value
        except ValueError:
            _LOGGER.error("Unknown Device Fault (%s)", self.data["device_fault"])
            return DeviceFault.Unknown.value

    @property
    def target_time(self) -> int:
        """Target Time."""
        return self.data["target_time"]

    @property
    def target_temperature(self) -> int:
        """Target Temperature."""
        return self.data["target_temperature"]

    @property
    def left_time(self) -> int:
        """Left Time."""
        return self.data["left_time"]

    @property
    def recipe_id(self) -> str:
        """Recipe ID."""
        return self.data["recipe_id"]

    @property
    def recipe_name(self) -> str:
        """Recipe name."""
        return RecipeName(RecipeId(self.data["recipe_id"]).name).value

    @property
    def appoint_time(self) -> int:
        """Appoint Time"""
        return self.data["appoint_time"]

    @property
    def food_quanty(self) -> FoodQuanty:
        """Food Quanty."""
        try:
            return FoodQuanty(self.data["food_quanty"])
        except ValueError:
            _LOGGER.error("Unknown FoodQuanty (%s)", self.data["food_quanty"])
            return FoodQuanty.Single

    @property
    def preheat_switch(self) -> int:
        """Preheat Switch"""
        try:
            return PreheatSwitch(self.data["preheat_switch"]).value
        except ValueError:
            _LOGGER.error("Unknown PreheatSwitch (%s)", self.data["preheat_switch"])
            return PreheatSwitch.Unknown.value

    @property
    def appoint_time_left(self) -> int:
        """Appoint Time"""
        return self.data["appoint_time_left"]

    @property
    def turn_pot(self) -> TurnPot:
        """Turn Pot"""
        try:
            return TurnPot(self.data["turn_pot"])
        except ValueError:
            _LOGGER.error("Unknown TurnPot (%s)", self.data["turn_pot"])
            return TurnPot.Unknown


class FryerMiot(MiotDevice):
    """Interface for AirFryer (careli.fryer.maf02)"""

    mapping = MIOT_MAPPING

    def __init__(
        self,
        ip: str = None,
        token: str = None,
        start_id: int = 0,
        debug: int = 0,
        lazy_discover: bool = True,
        model: str = "careli.fryer.maf02",
    ) -> None:
        super().__init__(ip, token, start_id, debug, lazy_discover)
        self._model = model

    @command(
        default_output=format_output(
            "",
            "Status: {result.status.name}\n"
            "Device Fault: {result.device_fault.name}\n"
            "Target Time: {result.target_time}\n"
            "Target Temperature: {result.target_temperature}\n"
            "Left Time: {result.left_time}\n"
            "Recipe ID: {result.recipe_id}\n"
            "Appoint Time: {result.appoint_time}\n"
            "Food Quanty: {result.food_quanty.name}\n"
            "Preheat Switch: {result.preheat_switc.name}\n"
            "Appoint Time Left: {result.appoint_time_left}\n"
            "Turn Pot: {result.turn_pot.name}\n",
        )
    )
    def status(self) -> FryerStatusMiot:
        """Retrieve properties."""
        return FryerStatusMiot(
            {
                prop["did"]: prop["value"] if prop["code"] == 0 else None
                for prop in self.get_properties_for_mapping()
            }
        )

    @command(
        click.argument("hours", type=int),
        default_output=format_output("Setting appoint time to {hours} hours"),
    )
    def appoint_time(self, hours: int):
        """Set appoint time hours."""
        if hours < 0 or hours > 24 * 60:
            raise DeviceException("Invalid value for a appoint time: %s" % hours)

        return self.set_property("appoint_time", hours)

    @command(
        click.argument("recipe_id", type=str),
        default_output=format_output("Setting recipe id to {recipe_id}"),
    )
    def recipe_id(self, recipe_id: str):
        """Set recipe id."""
        return self.set_property("recipe_id", recipe_id)

    @command(
        click.argument("food_quanty", type=int),
        default_output=format_output("Setting food quanty to {food_quanty}"),
    )
    def food_quanty(self, food_quanty: int):
        """Set food quantity."""
        if food_quanty < 0 or food_quanty > 5:
            raise DeviceException("Invalid value for food_quanty: %s" % food_quanty)
        return self.set_property("food_quanty", food_quanty)

    @command(
        click.argument("target_time", type=int),
        default_output=format_output("Setting target time to {target_time}"),
    )
    def target_time(self, target_time: int):
        """Set recipe id."""
        if target_time < 1 or target_time > 1440:
            raise DeviceException("Invalid value for target_time: %s" % target_time)
        return self.set_property("target_time", target_time)

    @command(
        click.argument("target_temperature", type=int),
        default_output=format_output(
            "Setting target temperature to {target_temperature}"
        ),
    )
    def target_temperature(self, target_temperature: int):
        """Set recipe id."""
        if target_temperature < 40 or target_temperature > 200:
            raise DeviceException(
                "Invalid value for target_temperature: %s" % target_temperature
            )
        return self.set_property("target_temperature", target_temperature)

    @command()
    def start_cook(self) -> None:
        """Start cook"""
        return self.call_action("start_cook")

    @command()
    def cancel_cooking(self) -> None:
        """Cancel cooking."""
        return self.call_action("cancel_cooking")

    @command()
    def pause(self) -> None:
        """Pause cook"""
        return self.call_action("pause")

    @command()
    def start_custom_cook(self, mode) -> None:
        """Start custom cook"""
        recipe_id = RecipeId(mode)
        command = RecipeToCommand[recipe_id.name].value
        mode_command = ",".join([str(x) for x in command])
        return self.call_action("start_custom_cook", mode_command)

    @command()
    def resume_cooking(self) -> None:
        """Resume cooking."""
        return self.call_action("resume_cooking")

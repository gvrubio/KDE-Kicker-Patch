/*
 *    SPDX-FileCopyrightText: 2013-2015 Eike Hein <hein@kde.org>
 *
 *    SPDX-License-Identifier: GPL-2.0-or-later
 */

import QtQuick
import QtQuick.Controls as QQC2

import org.kde.plasma.components as PlasmaComponents3

import "code/tools.js" as Tools

PlasmaComponents3.ItemDelegate {
    id: item

    required property int index
    required property bool isSeparator
    required property bool hasChildren
    required property bool isParent
    required property bool disabled
    required property bool hasActionList
    required property bool isNewlyInstalled
    required property string favoriteId
    required property url url
    required property string description
    required property string decoration
    required property string compactName
    required property var model // for display, which would shadow ItemDelegate
    required property var favoritesModel
    required property var baseModel

    property bool dialogDefaultRight: Application.layoutDirection !== Qt.RightToLeft
    property bool dragActive: false

    signal interactionConcluded
    signal openCategory(bool keyboardInitiated)

    text: model.display
    icon.name: decoration
    hoverEnabled: true

    // plain QQC2.Action: Kirigami.Action also creates a Shortcut and Connections per delegate,
    // which adds up when search results recreate hundreds of delegates per keystroke
    action: QQC2.Action {
        onTriggered: source => {
            if (item.dragActive) { return }
            if (!item.hasChildren) {
                item.baseModel.trigger(item.index, "", null);
                item.interactionConcluded()
            } else {
                item.openCategory(source instanceof KeyEvent)
            }
        }
    }

    function openActionMenu(x: real, y: real) : void {
        // actionList is costly to compute (jump lists, recent documents, ...), so only
        // fetch it from the model when the menu is opened, not on delegate creation
        const actionList = item.hasActionList ? item.model.actionList : [];
        Tools.fillActionMenu(i18n, ActionMenu, actionList, item.favoritesModel, item.favoriteId);
        if (!ActionMenu.actionList.length) {
            return
        }
        ActionMenu.visualParent = item;
        ActionMenu.delegate = item;
        ActionMenu.open(x, y);
    }

    MouseArea {
        id: mouseArea

        anchors.fill: parent

        acceptedButtons: Qt.RightButton

        onPressed: mouse => {
            if (item.hasActionList || item.favoriteId !== null) {
                item.openActionMenu(mouse.x, mouse.y);
            }
        }
    }

    contentItem: null

    Keys.onReturnPressed: event => action.trigger(event)
    Keys.onEnterPressed: event => action.trigger(event)
    Keys.onSpacePressed: event => action.trigger(event)
    Keys.onMenuPressed: {
        if (item.hasActionList || item.favoriteId !== null) {
            item.openActionMenu()
        }
    }
}
